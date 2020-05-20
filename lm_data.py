import time
import numpy
import copy
from ctypes import c_int8, c_int16
import threading
import configparser
import os
import my_serial
import usb_can_bridge
import norby_data


class LMData:
    def __init__(self, **kw):
        # настройки LM
        self.fabrication_number = 0
        self.address = 1
        self.baudrate = 9600
        self.serial_numbers = []
        self.debug = True
        self.crc_check = True
        for key in sorted(kw):
            if key == "serial_numbers":
                self.serial_numbers = kw.pop(key)
            elif key == "baudrate":
                self.baudrate = kw.pop(key)
            elif key == "address":
                self.address = kw.pop(key)
            elif key == "timeout":
                self.timeout = kw.pop(key)
            elif key == "port":
                self.port = kw.pop(key)
            elif key == "debug":
                self.debug = kw.pop(key)
            elif key == "crc":
                self.crc_check = kw.pop(key)
            else:
                pass
        # интерфейс работы с ITB - VCP-CAN
        self.usb_can = usb_can_bridge.MyUSBCANDevice(baudrate=self.baudrate,
                                                     serial_numbers=self.serial_numbers,
                                                     debug=False,  # self.debug,
                                                     crc=self.crc_check,
                                                     )
        # заготовка для хранения данных прибора
        self.general_data = []
        self.graph_interval = 3600
        # заготовка для хранения и отображения параметров работы прибора
        # заготовка для хранения результата циклограммы
        self.cycl_result_offset = 1152
        self.cycl_128B_part_num = 17
        self.cyclogram_result_data = [[] for i in range(self.cycl_128B_part_num)]
        # заготовка для хранения переменных общения с ПН1.1
        self.pl_iss_data = {"pl11_a": [],
                            "pl11_b": [],
                            "pl12": [],
                            "pl20": []
        }
        #
        self._close_event = threading.Event()
        self.parc_thread = threading.Thread(target=self.parc_data, args=(), daemon=True)
        self.data_lock = threading.Lock()
        # инициализация
        self.parc_thread.start()
        pass

    def send_cmd(self, mode="dbg_led_test", action="start"):
        req_param_dict = {"can_num": 0,
                          "dev_id": self.address,
                          "mode": "write",
                          "var_id": 2,
                          "offset": 16,
                          "d_len": 1,
                          "data": [0x01]}
        if action == "start":
            req_param_dict["data"] = [0x01]
        elif action == "stop":
            req_param_dict["data"] = [0xFF]
        if mode in "dbg_led_test":
            req_param_dict["offset"] = 16
        elif mode in "lm_init":
            req_param_dict["offset"] = 0
        elif mode in "dcr_mem_clear":
            req_param_dict["offset"] = 1
        elif mode in "iss_mem_clear":
            req_param_dict["offset"] = 2
        else:
            raise ValueError("Incorrect method parameter <mode>")
        self._print("send com<%s> <%s>" % (mode, action))
        self.usb_can.request(**req_param_dict)

    def read_cmd_status(self, mode="dbg_led_test"):
        req_param_dict = {"can_num": 0,
                          "dev_id": self.address,
                          "mode": "read",
                          "var_id": 3,
                          "offset": 16,
                          "d_len": 1,
                          "data": [0x01]}
        if mode in "dbg_led_test":
            req_param_dict["offset"] = 16
        elif mode in "lm_init":
            req_param_dict["offset"] = 0
        elif mode in "dcr_mem_clear":
            req_param_dict["offset"] = 1
        elif mode in "iss_mem_clear":
            req_param_dict["offset"] = 2
        else:
            raise ValueError("Incorrect method parameter <mode>")
        self._print("read com_status<%s>" % (mode))
        self.usb_can.request(**req_param_dict)

    def send_cmd_reg(self, mode="dbg_led_test", data=None):
        if data:
            req_param_dict = {"can_num": 0,
                              "dev_id": self.address,
                              "mode": "write",
                              "var_id": 4,
                              "offset": 16,
                              "d_len": len(data),
                              "data": data}
            if mode in "dbg_led_test":
                req_param_dict["offset"] = 0x30
            elif mode in "synch_time":
                req_param_dict["offset"] = 0x00
            elif mode in "const_mode":
                req_param_dict["offset"] = 0x04
            elif mode in "lm_mode":
                req_param_dict["offset"] = 0x10
            elif mode in "lm_pn_pwr_switch":
                req_param_dict["offset"] = 0x11
            elif mode in "pn_inhibit":
                req_param_dict["offset"] = 0x12
            elif mode in "all_mem_rd_ptr":
                req_param_dict["offset"] = 0x1A
            elif mode in "part_mem_rd_ptr":
                req_param_dict["offset"] = 0x1E
            elif mode in "pn_dcr_mode":
                req_param_dict["offset"] = 0x22
            elif mode in "pl11_a_outputs":
                req_param_dict["offset"] = 0x23
            elif mode in "pl11_b_outputs":
                req_param_dict["offset"] = 0x24
            elif mode in "pl12_outputs":
                req_param_dict["offset"] = 0x25
            elif mode in "pl20_outputs":
                req_param_dict["offset"] = 0x26
            elif mode in "cyclogram_start":
                req_param_dict["offset"] = 0x27
            else:
                raise ValueError("Incorrect method parameter <mode>")
            self._print("send com_reg<%s>: " % mode, data)
            self.usb_can.request(**req_param_dict)

    def read_cmd_reg(self, mode="dbg_led_test", leng=1):
        if leng >= 1:
            req_param_dict = {"can_num": 0,
                              "dev_id": self.address,
                              "mode": "read",
                              "var_id": 4,
                              "offset": 16,
                              "d_len": leng,
                              "data": []}
            if mode in "dbg_led_test":
                req_param_dict["offset"] = 0x30
            elif mode in "synch_time":
                req_param_dict["offset"] = 0x00
            elif mode in "const_mode":
                req_param_dict["offset"] = 0x04
            elif mode in "lm_mode":
                req_param_dict["offset"] = 0x10
            elif mode in "lm_pn_pwr_switch":
                req_param_dict["offset"] = 0x11
            elif mode in "pn_inhibit":
                req_param_dict["offset"] = 0x12
            elif mode in "all_mem_rd_ptr":
                req_param_dict["offset"] = 0x1A
            elif mode in "part_mem_rd_ptr":
                req_param_dict["offset"] = 0x1E
            elif mode in "pn_dcr_mode":
                req_param_dict["offset"] = 0x22
            elif mode in "pl11_a_outputs":
                req_param_dict["offset"] = 0x23
            elif mode in "pl11_b_outputs":
                req_param_dict["offset"] = 0x24
            elif mode in "pl12_outputs":
                req_param_dict["offset"] = 0x25
            elif mode in "pl20_outputs":
                req_param_dict["offset"] = 0x26
            elif mode in "cyclogram_start":
                req_param_dict["offset"] = 0x27
            else:
                raise ValueError("Incorrect method parameter <mode>")
            self._print("read com_reg<%s>" % mode)
            self.usb_can.request(**req_param_dict)

    def read_tmi(self, mode="beacon"):
        req_param_dict = {"can_num": 0,
                          "dev_id": self.address,
                          "mode": "read",
                          "var_id": 5,
                          "offset": 0,
                          "d_len": 128,
                          "data": []}
        if mode in "lm_beacon":
            req_param_dict["offset"] = 0
        elif mode in "lm_tmi":
            req_param_dict["offset"] = 128
        elif mode in "lm_full_tmi":
            req_param_dict["offset"] = 256
        else:
            raise ValueError("Incorrect method parameter <mode>")
        self._print("read tmi <%s>" % mode)
        self.usb_can.request(**req_param_dict)

    def read_cyclogram_result(self, part_num=0):
        req_param_dict = {"can_num": 0,
                          "dev_id": self.address,
                          "mode": "read",
                          "var_id": 5,
                          "offset": 0,
                          "d_len": 128,
                          "data": []}
        part_num = 16 if part_num > self.cycl_128B_part_num else part_num
        req_param_dict["offset"] = self.cycl_result_offset + part_num * 128
        self._print("read cyclogram result <offset %d>" % req_param_dict["offset"])
        self.usb_can.request(**req_param_dict)

    def read_mem(self, mode="mem_all"):
        req_param_dict = {"can_num": 0,
                          "dev_id": self.address,
                          "mode": "read",
                          "var_id": 7,
                          "offset": 0,
                          "d_len": 128,
                          "data": []}
        if mode in "mem_all":
            req_param_dict["offset"] = 0
        elif mode in "iss_mem":
            req_param_dict["offset"] = 128
        elif mode in "dcr_mem":
            req_param_dict["offset"] = 256
        else:
            raise ValueError("Incorrect method parameter <mode>")
        self._print("read <%s>" % mode)
        self.usb_can.request(**req_param_dict)

    def send_iss_instamessage(self, pl_type="pl11_a", data=None):
        req_param_dict = {"can_num": 0,
                          "dev_id": self.address,
                          "mode": "write",
                          "var_id": 9,
                          "offset": 0,
                          "d_len": 128,
                          "data": data}
        if pl_type is "pl11_a":
            req_param_dict["offset"] = 0*128
        elif pl_type is "pl11_b":
            req_param_dict["offset"] = 1*128
        elif pl_type is "pl12":
            req_param_dict["offset"] = 2*128
        elif pl_type is "pl20":
            req_param_dict["offset"] = 3*128
        else:
            raise ValueError("Incorrect method parameter <mode>")
        self._print("send instamessage <%s>" % pl_type)
        self.usb_can.request(**req_param_dict)

    def read_iss_instamessage(self, pl_type="pl11_a"):
        req_param_dict = {"can_num": 0,
                          "dev_id": self.address,
                          "mode": "read",
                          "var_id": 9,
                          "offset": 0,
                          "d_len": 128,
                          "data": []}
        if pl_type is "pl11_a":
            req_param_dict["offset"] = 0*128
        elif pl_type is "pl11_b":
            req_param_dict["offset"] = 1*128
        elif pl_type is "pl12":
            req_param_dict["offset"] = 2*128
        elif pl_type is "pl20":
            req_param_dict["offset"] = 3*128
        else:
            raise ValueError("Incorrect method parameter <pl_type>")
        self._print("read instamessage <%s>" % pl_type)
        self.usb_can.request(**req_param_dict)

    def parc_data(self):
        while True:
            time.sleep(0.01)
            id_var_row, data = self.usb_can.get_data()
            res1, rtr, res2, offset, var_id, dev_id = self.usb_can.process_id_var(id_var_row)
            with self.data_lock:
                if var_id == 5:  # переменная телеметрии
                    report_data = " ".join([("%04X" % var) for var in data])
                    self._print("process tmi <var_id = %d, offset %d>" % (var_id, offset), report_data)
                    parced_data = norby_data.frame_parcer(data)
                    if offset == 256:
                        self.manage_general_data(parced_data)
                    elif 1152 <= offset < 3328:
                        self.manaage_cyclogram_result_data(offset, data)
                    pass
                elif var_id == 7:  # переменная памяти
                    self._print("process mem <var_id = %d, offset %d>" % (var_id, offset))
                    parced_data = norby_data.frame_parcer(data)
                    self._print("process mem data", parced_data)
                    pass
                elif var_id == 3:  # статусы функций
                    self._print("process cmd_status <var_id = %d, offset %d>:" % (var_id, offset), data)
                    pass
                elif var_id == 4:  # статусные регистры
                    self._print("process cmd_regs <var_id = %d, offset %d>:" % (var_id, offset), data)
                    pass
                elif var_id == 9:  # результат общения с ПН
                    self._print("process instamessage <var_id = %d, offset %d>:" % (var_id, offset), list_to_str(data))
                    self.parc_instamessage_data(offset, data)
                    pass
            if self._close_event.is_set() is True:
                self._close_event.clear()
                return
        pass

    def manage_general_data(self, frame_data):
        if len(frame_data) >= 4:
            name_list = ["Time, s"]
            data_list = [int(time.perf_counter())]
            name_list.extend([var[0] for var in frame_data])
            data_list.extend([(self._get_number_from_str(var[1])) for var in frame_data])
            #
            try:
                if len(self.general_data) == 0:
                    for num in range(len(name_list)):
                        self.general_data.append([name_list[num], [data_list[num]]])
                else:
                    for num in range(min(len(data_list), len(self.general_data))):
                        self.general_data[num][1].append(data_list[num])
                # self.cut_general_data(self.graph_interval)
            #
            except Exception as error:
                self._print("m: manage_general_data <%s>" % error)
        else:
            self._print("m: manage_general_data frame_data_error")

    def reset_general_data(self):
        self.general_data = []

    def _get_number_from_str(self, str_var):
        try:
            try:
                number = float(str_var)
            except ValueError:
                number = int(str_var, 16)
            return number
        except Exception as error:
            self._print(error)
        return 0

    def cut_general_data(self, interval_s):
        if len(self.general_data) > 1:
            while self.general_data[0][1][-1] - self.general_data[0][1][0] >= interval_s:
                self.general_data.pop(0)
        pass

    # cyclogram result_data
    def manaage_cyclogram_result_data(self, offset, data):
        part_num = (offset - self.cycl_result_offset) // 128
        self.cyclogram_result_data[part_num] = data
        pass

    def get_cyclogram_result_str(self):
        report_str = "Row cyclogram result data:\n\n"
        with self.data_lock:
            for part in self.cyclogram_result_data:
                report_str += list_to_str(part) + '\n'
        return report_str

    def get_parc_cyclogram_result(self):
        report_str = "\nParced cyclogram result data:\n\n"
        cycl_result = []
        with self.data_lock:
            cycl_result = copy.deepcopy(self.cyclogram_result_data)
        # вычленение сырах данных
        report_str += "\nCyclogram result PL data:\n\n"
        bytes_num = 0
        for body in cycl_result[1:]:
            try:
                if body[0] == 0xF10F:
                    for u16_var in body[4:63]:
                        report_str += "%04X " % u16_var
                        bytes_num += 2
                        if (bytes_num % 64) == 0:
                            report_str += "\n"
            except IndexError:
                pass
        report_str += "\n"
        # вычленение сырах данных
        report_str += "\nCyclogram result PL data (reverse byte order in u32-words, special for PL1.1):\n\n"
        bytes_num = 0
        word_to_print = ["", "", "", ""]
        try:
            for body in cycl_result[1:]:
                if body[0] == 0xF10F:
                    for u16_var in body[4:63]:
                        bytes_num += 2
                        if (bytes_num % 4) == 0:
                            word_to_print[0] = "%02X" % ((u16_var >> 0) & 0xFF)
                            word_to_print[1] = "%02X " % ((u16_var >> 8) & 0xFF)
                            report_str += "".join(word_to_print)
                            word_to_print = ["", "", "", ""]
                        else:
                            word_to_print[2] = "%02X" % ((u16_var >> 0) & 0xFF)
                            word_to_print[3] = "%02X  " % ((u16_var >> 8) & 0xFF)
                        if (bytes_num % 64) == 0:
                            report_str += "\n"
        except IndexError:
            pass
        report_str += "\n"
        # разбор заголовка
        report_str += "\nCyclogram result header:\n\n"
        parced_data = norby_data.frame_parcer(cycl_result[0])
        for data in parced_data:
            report_str += "{:<30}".format(data[0]) + "\t{:}".format(data[1]) + "\n"
        return report_str


    # pl_iss instamessage data #
    def parc_instamessage_data(self, offset, data):
        try:
            leng = (data[63] & 0x1F) + 1
            leng = 30 if leng > 30 else leng
        except IndexError:
            return
        u32_data = []
        for num in range(32):  # 2 - ctrl_byte & address, leng - data
            try:
                u32_data.append((data[0+num*2] << 16) + (data[1+num*2] << 0))
            except IndexError:
                u32_data.append(0x00000000)
        if offset == 0*128:
            self.pl_iss_data["pl11_a"] = u32_data
        elif offset == 1*128:
            self.pl_iss_data["pl11_b"] = u32_data
        elif offset == 2*128:
            self.pl_iss_data["pl12"] = u32_data
        elif offset == 3*128:
            self.pl_iss_data["pl20"] = u32_data

    # LOG data #
    def get_log_file_title(self):
        name_str = ""
        return name_str

    def get_log_file_data(self):
        data_str = ""
        return data_str

    def _print(self, *args):
        if self.debug:
            print_str = "lmd: " + self.get_time()
            for arg in args:
                print_str += " " + str(arg)
            print(print_str)

    @staticmethod
    def get_time():
        return time.strftime("%H-%M-%S", time.localtime()) + " " + ("%.3f:" % time.perf_counter())


def value_from_bound(val, val_min, val_max):
    return max(val_min, min(val_max, val))


def list_to_str(input_list):
    return_str = " ".join(["%04X " % var for var in input_list])
    return return_str


if __name__ == "__main__":
    lm = LMData(address=6, debug=True, serial_numbers=["205135995748"])
    lm.usb_can.open_id()
    #
    print("тест отправки команд")
    lm.send_cmd(mode="dbg_led_test", action="start")
    for i in range(10):
        time.sleep(1)
        lm.read_cmd_status(mode="dbg_led_test")
    lm.send_cmd(mode="dbg_led_test", action="stop")
    for i in range(2):
        time.sleep(1)
        lm.read_cmd_status(mode="dbg_led_test")
    time.sleep(1)
    #
    print("тест записи командного регистра")
    lm.send_cmd_reg(mode="dbg_led_test", data=[0xEE])
    lm.read_cmd_reg(mode="dbg_led_test", leng=1)
    time.sleep(2)
    lm.send_cmd_reg(mode="dbg_led_test", data=[0x1E])
    lm.read_cmd_reg(mode="dbg_led_test", leng=1)
    time.sleep(2)
    #
    print("тест чтения телеметрии")
    lm.read_tmi(mode="lm_beacon")
    time.sleep(1)
    #
    print("тест чтения памяти")
    lm.read_mem(mode="mem_all")
    time.sleep(1)
    #
    pass
