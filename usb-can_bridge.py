"""
Библиотека для общения через устройтво USB-CAN bridge (за авторством А.А. Дорошика):
 -описание typeIdxMask
    uint32_t res1 : 1;
    uint32_t RTR : 1;
    uint32_t res2 : 1;
    uint32_t Offset : 21;
    uint32_t VarId : 4;
    uint32_t DevId : 4;
 -описаиние пасылки в CAN-USB:
    uint8_t ncan;
    uint8_t res1;
    typeIdxMask id;
    uint16_t leng;
    uint8_t data[8];
}typePacket;
"""
import serial
import serial.tools.list_ports
import threading
import time
import crc16
import copy


class MyUSBCANDevice(serial.Serial):
    def __init__(self, **kw):
        serial.Serial.__init__(self)
        self.serial_numbers = []  # это лист возможных серийников!!! (не строка)
        self.baudrate = 115200
        self.timeout = 0.01
        self.port = "COM0"
        self.row_data = b""
        self.read_timeout = 0.5
        self.request_num = 0
        self.debug = False
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
            else:
                pass
        # общие переменные
        self.com_queue = []  # очередь отправки
        self.request_num = 0
        self.nansw = 0  # неответы
        self.answer_data = []
        self.answer_data_buffer = []
        self.com_rec_flag = 0
        self.read_data = b""
        self.read_flag = 0
        self.state_string = {
            -3: "Связь потеряна",
            -2: "Устройство не отвечает",
            -1: "Не удалось установить связь",
            +0: "Подключите устройство",
            +1: "Связь в норме",
        }
        self.state = 0
        self.log_buffer = []
        # для работы с потоками
        self.read_write_thread = None
        self._close_event = threading.Event()
        self.read_write_thread = threading.Thread(target=self.thread_function, args=(), daemon=True)
        self.read_write_thread.start()
        self.log_lock = threading.Lock()
        self.com_send_lock = threading.Lock()
        self.ans_data_lock = threading.Lock()

    def open_id(self):  # функция для установки связи с КПА
        com_list = serial.tools.list_ports.comports()
        for com in com_list:
            self._print("Find:", str(com), com.serial_number)
            for serial_number in self.serial_numbers:
                self._print("ID comparison:", com.serial_number, serial_number)
                if com.serial_number is not None:
                    if com.serial_number.find(serial_number) >= 0:
                        self._print("Connection to:", com.device)
                        self.port = com.device
                        try:
                            self.open()
                            self._print("Success connection!")
                            self.state = 1
                            self.nansw = 0
                            return True
                        except serial.serialutil.SerialException as error:
                            self._print("Fail connection")
                            self._print(error)
        self.state = -1
        return False

    def _print(self, *args):
        if self.debug:
            print_str = get_time() + " "
            for arg in args:
                print_str += " " + str(arg)
            print(print_str)

    def close_id(self):
        self._print("Try to close comport <0x%s>:" % self.port)
        self.close()
        self.state = 0
        pass

    def reconnect(self):
        self.close_id()
        self.open_id()

    def request(self, can_num=0, dev_id=0, mode="read", var_id=0, offset=0, d_len=0, data=None):
        rtr = 0 if mode is "write" else 1
        real_len = min(d_len, len(data)) if mode is "write" else d_len
        part_offset = offset
        packets_list = []
        while real_len > 0:
            part_len = 8 if real_len >= 8 else real_len
            real_len -= 8
            finish = 1 if real_len <= 0 else 0
            id_var = ((dev_id & 0x0F) << 28) | ((var_id & 0x0F) << 24) | ((part_offset & 0x1FFFFF) << 3) | \
                     ((0x00 & 0x01) << 2) | ((rtr & 0x01) << 1) | ((0x00 & 0x01) << 0)
            packet_list = [can_num & 0x01, 0x00,
                           (id_var >> 0) & 0xFF, (id_var >> 8) & 0xFF,
                           (id_var >> 16) & 0xFF, (id_var >> 24) & 0xFF,
                           (part_len >> 0) & 0xFF, (part_len >> 8) & 0xFF]
            packet_list.extend(data[0+part_offset:part_len+part_offset])
            part_offset += 8
            packets_list.append([packet_list, rtr, finish])
        with self.com_send_lock:
            self.com_queue.extend(packets_list)
        self._print("Try to send command <0x%08X> (%s):" % (id_var, self._id_var_to_str(id_var)))

    def _id_var(self, id_var):
        """
        process id_var_value
        :param self:
        :param id_var: id_var according to title
        :return: егзду of id_var fields
        """
        dev_id = (id_var >> 28) & 0x0F
        var_id = (id_var >> 24) & 0x0F
        offset = (id_var >> 3) & 0x01FFFF
        res2 = (id_var >> 2) & 0x01
        rtr = (id_var >> 1) & 0x01
        res1 = (id_var >> 0) & 0x01

        return res1, rtr, res2, offset, var_id, dev_id

    def _id_var_to_str(self, id_var):
        ret_str = ""
        ret_str += "rtr: %d " % self._id_var(id_var)[1]
        ret_str += "offset: %d " % self._id_var(id_var)[3]
        ret_str += "var_id: %d " % self._id_var(id_var)[4]
        ret_str += "dev_id: %d " % self._id_var(id_var)[5]
        return ret_str

    def thread_function(self):
        try:
            while True:
                nansw = 0
                reprot_id_var = 0
                if self.is_open is True:
                    time.sleep(0.010)
                    # отправка команд
                    if self.com_queue:
                        with self.com_send_lock:
                            packet_to_send = self.com_queue.pop(0)
                            rtr = packet_to_send[1]
                            finish = packet_to_send[2]
                            data_to_send = packet_to_send[0]
                        if self.in_waiting:
                            self._print("In input buffer %d bytes" % self.in_waiting)
                            self.read(self.in_waiting)
                        try:
                            self.read(self.in_waiting)
                            self.write(bytes(data_to_send))
                            nansw = 1 if rtr == 1 else 0
                            self._print("Send packet: ", bytes_array_to_str(data_to_send))
                        except serial.serialutil.SerialException as error:
                            self.state = -3
                            self._print("Send error: ", error)
                            pass
                        with self.log_lock:
                            self.log_buffer.append(get_time() + bytes_array_to_str(bytes(data_to_send)))
                        # прием ответа: ждем ответа timeout ms только в случае rtr=1
                        buf = bytearray(b"")
                        read_data = bytearray(b"")
                        time_start = time.perf_counter()
                        while rtr:
                            time.sleep(0.01)
                            timeout = time.perf_counter() - time_start
                            if timeout >= self.read_timeout:
                                break
                            try:
                                read_data = self.read(128)
                                self.read_data = read_data
                            except (TypeError, serial.serialutil.SerialException, AttributeError) as error:
                                self.state = -3
                                self._print("Receive error: ", error)
                                pass
                            if read_data:
                                self._print("Receive data with timeout <%.3f>: " % self.timeout, bytes_array_to_str(read_data))
                                with self.log_lock:
                                    self.log_buffer.append(get_time() + bytes_array_to_str(read_data))
                                read_data = buf + bytes(read_data)  # прибавляем к новому куску старый кусок
                                self._print("Data to process: ", bytes_array_to_str(read_data))
                                if len(read_data) >= 4:
                                    if read_data[0] == 0x00 or read_data[0] == 0x01:
                                        data_len = int.from_bytes(read_data[6:8], byteorder="little")
                                        if len(read_data) >= data_len + 8:  # проверка на достаточную длину приходящего пакета
                                            nansw -= 1
                                            self.state = 1
                                            rtr = 0
                                            if len(self.answer_data_buffer) == 0:
                                                id_var = int.from_bytes(read_data[2:6], byteorder="little")
                                            self.answer_data_buffer.extend(read_data[8:8 + data_len])
                                            if finish:
                                                with self.ans_data_lock:
                                                    self.answer_data.append([id_var,
                                                                             self.answer_data_buffer])
                                                    self._print("Id_var = 0x%08X (%s), read data: " %
                                                                (id_var, self._id_var_to_str(id_var)),
                                                                bytes_array_to_str(self.answer_data_buffer))
                                                self.answer_data_buffer = []
                                        else:
                                            buf = read_data
                                            read_data = bytearray(b"")
                                    else:
                                        buf = read_data[1:]
                                        read_data = bytearray(b"")
                                else:
                                    buf = read_data
                                    read_data = bytearray(b"")
                                pass
                            else:
                                pass
                else:
                    pass
                if nansw == 1:
                    self.state = -3
                    self.nansw += 1
                    self._print("Timeout error")
                if self._close_event.is_set() is True:
                    self._close_event.clear()
                    return
        except Exception as error:
            self._print(error)
        pass

    def get_log(self):
        with self.log_lock:
            log = copy.deepcopy(self.log_buffer)
            self.log_buffer = []
        return log


def get_time():
    return time.strftime("%H-%M-%S", time.localtime()) + "." + ("%.3f:" % time.perf_counter()).split(".")[1]


def str_to_list(send_str):  # функция, которая из последовательности шестнадцетиричных слов в строке без
    send_list = []  # идентификатора 0x делает лист шестнадцетиричных чисел
    send_str = send_str.split(' ')
    for i, ch in enumerate(send_str):
        send_str[i] = ch
        send_list.append(int(send_str[i], 16))
    return send_list


def bytes_array_to_str(bytes_array):
    bytes_string = ""
    for num, ch in enumerate(bytes_array):
        byte_str = "" if num % 2 else " "
        byte_str += ("%02X" % bytes_array[num])
        bytes_string += byte_str
    return bytes_string


if __name__ == "__main__":
    my_can = MyUSBCANDevice(serial_numbers=["0000ACF00000"], debug=True)
    my_can.open_id()
    # Проверка коанды зеркала
    my_can.request(can_num=0, dev_id=6, mode="write", var_id=4, offset=0, d_len=18, data=[j for j in range(18)])
    my_can.request(can_num=0, dev_id=6, mode="read", var_id=4, offset=0, d_len=17, data=[])
    time.sleep(2)
    my_can.request(can_num=0, dev_id=6, mode="read", var_id=4, offset=1, d_len=17, data=[])
    time.sleep(2)
    print(my_can.answer_data)
    pass
