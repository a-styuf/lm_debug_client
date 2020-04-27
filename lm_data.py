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
        self.debug = []
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
                                                     debug=False,
                                                     crc=self.crc_check,
                                                     )
        # заготовка для хранения данных прибора
        self.general_data = []
        self.graph_interval = 3600
        # заготовка для хранения и отображения параметров работы прибора
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
                req_param_dict["offset"] = 16
            elif mode in "lm_mode":
                req_param_dict["offset"] = 0
            elif mode in "lm_pn_pwr_switch":
                req_param_dict["offset"] = 1
            elif mode in "pn_inhibit":
                req_param_dict["offset"] = 2
            elif mode in "all_mem_rd_ptr":
                req_param_dict["offset"] = 4
            elif mode in "pn_dcr_mode":
                req_param_dict["offset"] = 8
            elif mode in "dbg_cyclogram_start":
                req_param_dict["offset"] = 17
            else:
                raise ValueError("Incorrect method parameter <mode>")
            self._print("send com_reg<%s>" % mode)
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
                req_param_dict["offset"] = 16
            elif mode in "lm_mode":
                req_param_dict["offset"] = 0
            elif mode in "lm_pn_pwr_switch":
                req_param_dict["offset"] = 1
            elif mode in "pn_inhibit":
                req_param_dict["offset"] = 2
            elif mode in "all_mem_rd_ptr":
                req_param_dict["offset"] = 4
            elif mode in "dbg_cyclogram_start":
                req_param_dict["offset"] = 17
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

    def send_start_single_cyclogram_num(self, cyclogram_num):
        pass

    def send_start_cyclic_cyclograms(self):
        pass

    def send_stop_any_cyclograms(self):
        pass

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
        return time.strftime("%H-%M-%S", time.localtime()) + "." + ("%.3f:" % time.perf_counter()).split(".")[1]


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
