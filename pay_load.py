# encoding: utf-8
# module pay_load
"""
    Soft-model for payload control
"""
from PyQt5 import QtWidgets, QtCore, QtGui
import time

class PayLoad_11(QtCore.QObject):
    instamessage_signal = QtCore.pyqtSignal(int)

    def __init__(self, parent, lm=None, pl_type="pl11_a"):
        super().__init__(parent)
        #
        self.debug = True
        self.voltage = 0
        self.current = 0
        self.power = 0
        self.temperature = 0
        self.output_state = 0
        self.input_state = 0
        self.lm = lm  # чеерез данный объект происходит общение с модулем сопряжения
        self.pl_type = pl_type
        # создание очереди заданий для чтения
        self.read_data_timer = QtCore.QTimer()
        self.read_counter = 0
        self.readed_data = []
        pass

    def set_out(self, rst_fpga=True, rst_leon=True):
        rst_fpga_int = 1 if rst_fpga else 0
        rst_leon_int = 1 if rst_leon else 0
        output_state = ((rst_leon_int & 0x01) << 1) | ((rst_fpga_int & 0x01) << 0)
        if self.pl_type is "pl11_a":
            self.lm.send_cmd_reg(mode="pl11_a_outputs", data=[output_state])
        elif self.pl_type is "pl11_b":
            self.lm.send_cmd_reg(mode="pl11_b_outputs", data=[output_state])

    def write_data(self, u32_addr=None, u32_word=None):
        ctrl_byte = 0xC0
        data_len = 1
        send_data = [0x00 for i in range(128)]
        send_data[0:4] = self.u32_to_list(u32_addr)
        send_data[4:8] = self.u32_to_list(u32_word)
        send_data[124:128] = [0x00, 0x00, 0x00, ctrl_byte + (data_len - 1)]
        self.lm.send_iss_instamessage(pl_type=self.pl_type, data=send_data)
        pass

    def read_req_data(self, u32_addr=None):
        if self.read_counter == 0:
            # запись запроса для общения с уровнем приложения
            ctrl_byte = 0x80
            data_len = 1
            send_data = [0x00 for i in range(128)]
            send_data[0:4] = self.u32_to_list(u32_addr)
            send_data[124:128] = [0x00, 0x00, 0x00, ctrl_byte + (data_len - 1)]
            self.lm.send_iss_instamessage(pl_type=self.pl_type, data=send_data)
            #
            self.read_counter = 1
            self.read_data_timer.singleShot(100, self.read_req_data)
        elif self.read_counter == 1:
            self.lm.read_iss_instamessage(pl_type=self.pl_type)
            #
            self.read_counter = 2
            self.read_data_timer.singleShot(200, self.read_req_data)
        elif self.read_counter == 2:
            self.read_counter = 0
            try:
                self.instamessage_signal.emit(self.lm.pl_iss_data["pl11_a"][1])
            except Exception as error:
                pass
                self._print(error)
        pass

    @staticmethod
    def u32_to_list(u32_data):
        if u32_data:
            return [(u32_data >> 24) & 0xFF, (u32_data >> 16) & 0xFF, (u32_data >> 8) & 0xFF, (u32_data >> 0) & 0xFF]
        else:
            return [0, 0, 0, 0]

    def get_out_int(self, mode="int"):
        interrupt = 0
        return interrupt

    @staticmethod
    def get_time():
        return time.strftime("%H-%M-%S", time.localtime()) + "." + ("%.3f:" % time.perf_counter()).split(".")[1]

    def _print(self, *args):
        if self.debug:
            print_str = "dvw: " + self.get_time()
            for arg in args:
                print_str += " " + str(arg)
            print(print_str)
