import time
import numpy
import copy
from ctypes import c_int8, c_int16
import threading
import configparser
import os
import my_serial


class LMData:
    def __init__(self, **kw):
        # настройки LM
        self.fabrication_number = 0
        self.address = 1
        self.channel_num = 2  # максимум 4
        self.baudrate = 9600
        self.serial_numbers = []
        self.debug = []
        self.crc_check = True
        for key in sorted(kw):
            if key == "serial_numbers":
                self.serial_numbers = kw.pop(key)
            elif key == "baudrate":
                self.baudrate = kw.pop(key)
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
        # интерфейс работы с ITB - virtual com port
        self.serial = my_serial.MySerial(baudrate=self.baudrate, serial_numbers=self.serial_numbers, debug=self.debug,
                                         crc=self.crc_check)
        # заготовка для хранения данных прибора
        self.general_data_name = ["Time, s", "Pwr switch, hex"]
        self.pwr_chan_names = ["LM", "PL11A", "PL11B", "PL12", "PL20", "PL_DCR1", "PL_DCR2"]
        self.voltage_data_name = [("U_%s,V" % name) for name in self.pwr_chan_names]
        self.current_data_name = [("I_%s,A" % name) for name in self.pwr_chan_names]
        self.temperature_data_name = [("T_%s,°C" % name) for name in self.pwr_chan_names]
        self.general_data = [0. for i in range(len(self.general_data_name))]
        self.voltage_data = [0. for i in range(len(self.voltage_data_name))]
        self.current_data = [0. for i in range(len(self.current_data_name))]
        self.temperature_data = [0. for i in range(len(self.temperature_data_name))]
        # заготовка для хранения и отображения параметров работы прибора
        self._close_event = threading.Event()
        self.parc_thread = threading.Thread(target=self.parc_data, args=(), daemon=True)
        self.data_lock = threading.Lock()
        # инициализация
        self.parc_thread.start()
        pass

    def send_cmd(self, mode="mirror", data=None):
        if mode in "mirror":
            self.serial.request(cmd=0x00, data=data)
        elif mode in "pwr_on_off":
            self.serial.request(cmd=0x01, data=data)
        elif mode in "pwr_tmi":
            self.serial.request(cmd=0x02, data=data)
        elif mode in "pwr_on_off_separately":
            self.serial.request(cmd=0x06, data=data)
        else:
            self.serial.request(cmd=0x00, data=data)

    def parc_data(self):
        while True:
            time.sleep(0.01)
            data = []
            with self.serial.ans_data_lock:
                if self.serial.answer_data:
                    data = copy.deepcopy(self.serial.answer_data)
                    self.serial.answer_data = []
            for var in data:
                if var[0] == 0x00:  # ответ на зеркало
                    pass
                elif var[0] == 0x01:  # pwr control
                    pass
                elif var[0] == 0x02:  # pwr tmi
                    self.parc_power_data(var[1])
            if self._close_event.is_set() is True:
                self._close_event.clear()
                return
        pass

    def parc_power_data(self, row_data):
        self.general_data[0] = time.perf_counter()
        self.general_data[1] = int.from_bytes(row_data[0:4], signed=False, byteorder="big")
        self.voltage_data[0] = int.from_bytes(row_data[4:6], signed=True, byteorder="big") / 256
        self.current_data[0] = int.from_bytes(row_data[6:8], signed=True, byteorder="big") / 256
        self.voltage_data[1] = int.from_bytes(row_data[8:10], signed=True, byteorder="big") / 256
        self.current_data[1] = int.from_bytes(row_data[10:12], signed=True, byteorder="big") / 256
        self.voltage_data[2] = int.from_bytes(row_data[12:14], signed=True, byteorder="big") / 256
        self.current_data[2] = int.from_bytes(row_data[14:16], signed=True, byteorder="big") / 256
        self.voltage_data[3] = int.from_bytes(row_data[16:18], signed=True, byteorder="big") / 256
        self.current_data[3] = int.from_bytes(row_data[18:20], signed=True, byteorder="big") / 256
        self.voltage_data[4] = int.from_bytes(row_data[20:22], signed=True, byteorder="big") / 256
        self.current_data[4] = int.from_bytes(row_data[22:24], signed=True, byteorder="big") / 256
        self.voltage_data[5] = int.from_bytes(row_data[24:26], signed=True, byteorder="big") / 256
        self.current_data[5] = int.from_bytes(row_data[26:28], signed=True, byteorder="big") / 256
        self.voltage_data[6] = int.from_bytes(row_data[28:30], signed=True, byteorder="big") / 256
        self.voltage_data[6] = int.from_bytes(row_data[30:32], signed=True, byteorder="big") / 256
        pass

    def get_log_file_title(self):
        name_str = ";".join(self.general_data_name) + ";"
        name_str += ";".join(self.voltage_data_name) + ";"
        name_str += ";".join(self.current_data_name) + ";"
        name_str += ";".join(self.temperature_data_name) + ";"
        return name_str

    def get_log_file_data(self):
        name_str = ";".join(["%.3g" % var for var in self.general_data]) + ";"
        name_str += ";".join(["%.3g" % var for var in self.voltage_data]) + ";"
        name_str += ";".join(["%.3g" % var for var in self.current_data]) + ";"
        name_str += ";".join(["%.3g" % var for var in self.temperature_data]) + ";"
        return name_str


def value_from_bound(val, val_min, val_max):
    return max(val_min, min(val_max, val))


def list_to_str(input_list):
    return_str = " ".join(["%04X " % var for var in input_list])
    return return_str
