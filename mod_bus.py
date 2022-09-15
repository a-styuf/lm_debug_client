import serial
import time
import threading
import serial.tools.list_ports
import crc16
import copy


class InternalBus(serial.Serial):
    def __init__(self, **kw):
        serial.Serial.__init__(self)
        self.serial_numbers = []  # это лист возможных серийников!!! (не строка)
        self.baudrate = 125000
        self.timeout = 0.010
        self.port = "COM0"
        self.row_data = b""
        for key in sorted(kw):
            if key == "serial_numbers":
                self.serial_numbers = kw.pop(key)
            elif key == "baudrate":
                self.baudrate = kw.pop(key)
            elif key == "timeout":
                self.baudrate = kw.pop(key)
            elif key == "port":
                self.baudrate = kw.pop(key)
            else:
                pass
        # для работы с потоками
        self.reading_thread = None
        self._close_event = threading.Event()
        self.reading_thread = threading.Thread(target=self.reading_thread_function, args=())
        self.reading_thread.start()
        self.lock = threading.Lock()
        self.serial_lock = threading.Lock()
        # общие переменные
        self.read_data = b""
        self.work_data = b""
        self.read_flag = 0
        self.error_string = "No error"
        self.state = 0
        self.log_buffer = []

    def open_id(self):  # функция для установки связи с КПА
        com_list = serial.tools.list_ports.comports()
        for com in com_list:
            print(com)
            for serial_number in self.serial_numbers:
                print(com.serial_number, serial_number)
                if com.serial_number is not None:
                    if com.serial_number.find(serial_number) >= 0:
                        # print(com.device)
                        self.port = com.device
                        try:
                            self.open()
                        except serial.serialutil.SerialException as error:
                            self.error_string = str(error)
                        self.state = 1
                        self.error_string = "Переподключение успешно"
                        return True
        self.state = 0
        return False
        pass

    def request(self, ad=0x05, fc=0x03, ar=0x0001, lr=0x01, dr=0x00, dl=None, p_function=None):
        """

        :param ad:
        :param fc:
        :param ar:
        :param lr:
        :param dr:
        :param dl:
        :param p_function: ссылка на функцию для разбора ответа
        :return:
        """
        data_to_send = []
        if fc == 0x03:  # F3
            data_to_send = [ad, fc, (ar >> 8) & 0xFF, (ar >> 0) & 0xFF, 0x00, lr]
        elif fc == 0x06:  # F6
            data_to_send = [ad, fc, (ar >> 8) & 0xFF, (ar >> 0) & 0xFF, (dr >> 8) & 0xFF, (dr >> 0) & 0xFF]
        elif fc == 0x10:  # F16
            data_to_send = [ad, fc, (ar >> 8) & 0xFF, (ar >> 0) & 0xFF, 0x00, lr, (lr*2) & 0xFF]
            data_to_send.extend(dl)
        crc16_reg = crc16.calc_modbus_crc16_bytes(data_to_send)
        data_to_send.extend(crc16_reg)
        try:
            if self.is_open:
                with self.serial_lock:
                    self.write(bytes(data_to_send))
        except serial.serialutil.SerialException as error:
            pass

    def serial_close(self):
        self._close_event.set()
        self.reading_thread.join()
        self.close()

    def reading_thread_function(self):
        buf = bytearray(b"")
        read_data = bytearray(b"")
        bad_packet_barray = bytearray(b"")
        while True:
            time.sleep(0.001)
            if self.is_open is True:
                try:
                    read_data = bytearray(b"")
                    with self.serial_lock:
                        if self.in_waiting:
                            read_data = self.read(256)
                    self.read_data = read_data
                except (TypeError, serial.serialutil.SerialException, AttributeError):
                    read_data = bytearray(b"")
                    pass
                if read_data:
                    # print(len(read_data), ": ", bytes_array_to_str(read_data))
                    pass
                read_data = buf + bytes(read_data)  # прибавляем к новому куску старый кусок
                if read_data:
                    leng = 0
                    bad_packet_flag = 0
                    error_packet_flag = 0
                    # print(bytes_array_to_str(read_data))
                    if len(read_data) >= 5:
                        if read_data[1] & 0x80:
                            if len(read_data) >= 5:  # проверка на запрос
                                if crc16.calc_modbus_crc16_bytes(read_data[0:5]) == [0, 0]:
                                    leng = 5
                                    error_packet_flag = 1
                            if leng == 0 and (len(read_data) >= 5):  # проверка на ответ
                                if crc16.calc_modbus_crc16_bytes(read_data[0:5]) == [0, 0]:
                                    leng = 5
                                    error_packet_flag = 1
                                else:
                                    bad_packet_flag = 1
                        elif read_data[1] == 0x03:
                            if len(read_data) >= 8:  # проверка на запрос
                                if crc16.calc_modbus_crc16_bytes(read_data[0:8]) == [0, 0]:
                                    leng = 8
                            if leng == 0 and (len(read_data) >= 5 + read_data[2]):  # проверка на ответ
                                if crc16.calc_modbus_crc16_bytes(read_data[0:5 + read_data[2]]) == [0, 0]:
                                    leng = 5 + read_data[2]
                                else:
                                    bad_packet_flag = 1
                        elif read_data[1] == 0x06:
                            if len(read_data) >= 8:  # проверка на запрос
                                if crc16.calc_modbus_crc16_bytes(read_data[0:8]) == [0, 0]:
                                    leng = 8
                                else:
                                    bad_packet_flag = 1
                            if leng == 0 and len(read_data) >= 8 and read_data[4] == 0x00 and read_data[5] == 0x00:  # ответ
                                if crc16.calc_modbus_crc16_bytes(read_data[0:8]) == [0, 0]:
                                    leng = 8
                                else:
                                    bad_packet_flag = 1
                        elif read_data[1] == 0x10:
                            if leng == 0 and len(read_data) >= 8:  # ответ
                                if crc16.calc_modbus_crc16_bytes(read_data[0:8]) == [0, 0]:
                                    leng = 8
                                else:
                                    bad_packet_flag = 1
                            if len(read_data) >= 9 + read_data[6]:
                                if crc16.calc_modbus_crc16_bytes(read_data[0:9 + read_data[6]]) == [0, 0]:
                                    leng = 9 + read_data[6]
                                else:
                                    bad_packet_flag = 1
                        elif read_data[0] == 0xFF: # широковещательная команда
                            if len(read_data) >= 8:  # проверка на запрос
                                if crc16.calc_modbus_crc16_bytes(read_data[0:8]) == [0, 0]:
                                    leng = 8
                                else:
                                    bad_packet_flag = 1
                        else:
                            bad_packet_flag = 1
                    if leng:  # пакет разобрался
                        self.work_data = read_data[0:leng]
                        buf = read_data[leng:]
                        if bad_packet_barray:
                            with self.lock:
                                self.log_buffer.append(get_time() + "%02d: 0x" % len(bad_packet_barray) + bytes_array_to_str(bad_packet_barray) + " :bad")
                                bad_packet_barray = bytearray(b"")
                        with self.lock:
                            if error_packet_flag:
                                self.log_buffer.append(get_time() +
                                                       "%02d: MB error: 0x" % leng + bytes_array_to_str(self.work_data) +
                                                       self.read_data_parcing())
                            else:
                                self.log_buffer.append(get_time() +
                                                       "%02d: 0x" % leng + bytes_array_to_str(self.work_data) +
                                                       self.read_data_parcing())
                        pass
                    elif bad_packet_flag:
                        bad_packet_barray += read_data[0:1]
                        buf = read_data[1:]
                    else:
                        with self.lock:
                            # self.log_buffer.append(get_time() + "%02d: 0x" % leng + bytes_array_to_str(read_data))
                            pass
                        buf = read_data[0:]
                        # print("normal %d- " % len(buf), bytes_array_to_str(buf))
                else:
                    pass
            else:
                pass
            if self._close_event.is_set() is True:
                self._close_event.clear()
                return
        pass

    def get_log(self):
        with self.lock:
            log = copy.deepcopy(self.log_buffer)
            self.log_buffer = []
        return log

    def read_flag_check(self):
        if self.read_flag == 1:
            self.read_flag = 0
            return 1
        else:
            return 0

    def read_data_parcing(self):  # дополняется при необходимости
        return ""


def get_time():
    return time.strftime("%H-%M-%S", time.localtime()) + "." + ("%.3f: " % time.perf_counter()).split(".")[1]


def str_to_list(send_str):  # функция, которая из последовательности шестнадцетиричных слов в строке без
    send_list = []  # идентификатора 0x делает лист шестнадцетиричных чисел
    send_str = send_str.split(' ')
    for i, ch in enumerate(send_str):
        send_str[i] = ch
        send_list.append(int(send_str[i], 16))
    return send_list


def bytes_array_to_str(bytes_array):
    bytes_string = ""
    for i, ch in enumerate(bytes_array):
        byte_str = (" %02X" % bytes_array[i])
        bytes_string += byte_str
    return bytes_string
