# encoding: utf-8
# module pay_load
"""
    Soft-model for payload control
"""
from PyQt5 import QtWidgets, QtCore, QtGui
import time
import lm_data


class PayLoad(QtCore.QObject):
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
        self.readed_data = None
        pass

    def set_out(self, rst_fpga=True, rst_leon=True, n_reset=True, spi_sel=True, ext_reset=True):
        rst_fpga_int = 1 if rst_fpga else 0
        rst_leon_int = 1 if rst_leon else 0
        output_state = ((rst_leon_int & 0x01) << 1) | ((rst_fpga_int & 0x01) << 0)
        if self.pl_type == "pl11_a":
            self.lm.send_cmd_reg(mode="pl11_a_outputs", data=[output_state])
        elif self.pl_type == "pl11_b":
            self.lm.send_cmd_reg(mode="pl11_b_outputs", data=[output_state])
        elif self.pl_type == "pl12":
            n_reset_int = 1 if n_reset else 0
            spi_sel_int = 1 if spi_sel else 0
            output_state = ((n_reset_int & 0x01) << 1) | ((spi_sel_int & 0x01) << 0)
            self.lm.send_cmd_reg(mode="pl12_outputs", data=[output_state])
        elif self.pl_type == "pl20":
            ext_reset_int = 1 if ext_reset else 0
            output_state = ext_reset_int & 0x01
            self.lm.send_cmd_reg(mode="pl20_outputs", data=[output_state])

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
            self.readed_data = None
            # запись запроса для общения с уровнем приложения
            ctrl_byte = 0x80
            data_len = 1
            send_data = [0x00 for i in range(128)]
            send_data[0:4] = self.u32_to_list(u32_addr)
            send_data[124:128] = [0x00, 0x00, 0x00, ctrl_byte + (data_len - 1)]
            self.lm.send_iss_instamessage(pl_type=self.pl_type, data=send_data)
            #
            self.read_counter = 1
            self.read_data_timer.singleShot(200, self.read_req_data)
        elif self.read_counter == 1:
            self.lm.read_iss_instamessage(pl_type=self.pl_type)
            #
            self.read_counter = 2
            self.read_data_timer.singleShot(300, self.read_req_data)
        elif self.read_counter == 2:
            self.read_counter = 0
            try:
                self.instamessage_signal.emit(self.lm.pl_iss_data[self.pl_type][1])
                self._print("read u32_word %08X" % self.lm.pl_iss_data[self.pl_type][1])
            except Exception as error:
                self._print(error)
                self.instamessage_signal.emit(0)
                self._print("error read u32_word")
        pass

    def read_req_data_pl20(self, u16_addr=None):
        if self.read_counter == 0:
            self.readed_data = None
            # запись запроса для общения с уровнем приложения
            send_data = [0x00 for i in range(128)]
            send_data[0] = 0xAA
            send_data[1] = 0x01
            send_data[2] = (u16_addr >> 8) & 0xFF
            send_data[3] = (u16_addr >> 0) & 0xFF
            send_data[4] = self.crc8_calc_for_pn_20(send_data, 4)
            send_data[5] = 0x55
            send_data[124:128] = [0x00, 0x00, 0x00, 6]
            self.lm.send_iss_instamessage(pl_type=self.pl_type, data=send_data)
            #
            self.read_counter = 1
            self.read_data_timer.singleShot(200, self.read_req_data_pl20)
        elif self.read_counter == 1:
            self.lm.read_iss_instamessage(pl_type=self.pl_type)
            #
            self.read_counter = 2
            self.read_data_timer.singleShot(300, self.read_req_data_pl20)
        elif self.read_counter == 2:
            self.read_counter = 0
            try:
                self.instamessage_signal.emit((self.lm.pl_iss_data[self.pl_type][2] << 8) + (self.lm.pl_iss_data[self.pl_type][3]))
                self._print("read u16_word %04X" % ((self.lm.pl_iss_data[self.pl_type][2] << 8) + (self.lm.pl_iss_data[self.pl_type][3])))
            except Exception as error:
                self._print(error)
                self.instamessage_signal.emit(0)
                self._print("error read u16_word")
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
        return time.strftime("%H-%M-%S", time.localtime()) + " " + ("%.3f:" % time.perf_counter())

    def _print(self, *args):
        if self.debug:
            print_str = "pld: " + self.get_time()
            for arg in args:
                print_str += " " + str(arg)
            print(print_str)

    @staticmethod
    def crc8_calc_for_pn_20(data_list, length):
        crc_table = [0x00, 0x07, 0x0E, 0x09, 0x1C, 0x1B, 0x12, 0x15, 0x38, 0x3F, 0x36, 0x31, 0x24, 0x23, 0x2A, 0x2D,
                     0x70, 0x77, 0x7E, 0x79, 0x6C, 0x6B, 0x62, 0x65, 0x48, 0x4F, 0x46, 0x41, 0x54, 0x53, 0x5A, 0x5D,
                     0xE0, 0xE7, 0xEE, 0xE9, 0xFC, 0xFB, 0xF2, 0xF5, 0xD8, 0xDF, 0xD6, 0xD1, 0xC4, 0xC3, 0xCA, 0xCD,
                     0x90, 0x97, 0x9E, 0x99, 0x8C, 0x8B, 0x82, 0x85, 0xA8, 0xAF, 0xA6, 0xA1, 0xB4, 0xB3, 0xBA, 0xBD,
                     0xC7, 0xC0, 0xC9, 0xCE, 0xDB, 0xDC, 0xD5, 0xD2, 0xFF, 0xF8, 0xF1, 0xF6, 0xE3, 0xE4, 0xED, 0xEA,
                     0xB7, 0xB0, 0xB9, 0xBE, 0xAB, 0xAC, 0xA5, 0xA2, 0x8F, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9D, 0x9A,
                     0x27, 0x20, 0x29, 0x2E, 0x3B, 0x3C, 0x35, 0x32, 0x1F, 0x18, 0x11, 0x16, 0x03, 0x04, 0x0D, 0x0A,
                     0x57, 0x50, 0x59, 0x5E, 0x4B, 0x4C, 0x45, 0x42, 0x6F, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7D, 0x7A,
                     0x89, 0x8E, 0x87, 0x80, 0x95, 0x92, 0x9B, 0x9C, 0xB1, 0xB6, 0xBF, 0xB8, 0xAD, 0xAA, 0xA3, 0xA4,
                     0xF9, 0xFE, 0xF7, 0xF0, 0xE5, 0xE2, 0xEB, 0xEC, 0xC1, 0xC6, 0xCF, 0xC8, 0xDD, 0xDA, 0xD3, 0xD4,
                     0x69, 0x6E, 0x67, 0x60, 0x75, 0x72, 0x7B, 0x7C, 0x51, 0x56, 0x5F, 0x58, 0x4D, 0x4A, 0x43, 0x44,
                     0x19, 0x1E, 0x17, 0x10, 0x05, 0x02, 0x0B, 0x0C, 0x21, 0x26, 0x2F, 0x28, 0x3D, 0x3A, 0x33, 0x34,
                     0x4E, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5C, 0x5B, 0x76, 0x71, 0x78, 0x7F, 0x6A, 0x6D, 0x64, 0x63,
                     0x3E, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2C, 0x2B, 0x06, 0x01, 0x08, 0x0F, 0x1A, 0x1D, 0x14, 0x13,
                     0xAE, 0xA9, 0xA0, 0xA7, 0xB2, 0xB5, 0xBC, 0xBB, 0x96, 0x91, 0x98, 0x9F, 0x8A, 0x8D, 0x84, 0x83,
                     0xDE, 0xD9, 0xD0, 0xD7, 0xC2, 0xC5, 0xCC, 0xCB, 0xE6, 0xE1, 0xE8, 0xEF, 0xFA, 0xFD, 0xF4, 0xF3]
        #
        crc = 0x00
        for i in range(length):
            crc = crc_table[crc ^ (data_list[i] & 0xFF)]
        return crc


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    pass
