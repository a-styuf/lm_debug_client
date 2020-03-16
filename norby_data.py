'''
    модуль собирающий в себе стандартизованные функции разбора данных
    Стандарт:
    параметры:
        frame - в виде листа с данными
    возвращает:
        table_list - список подсписков (подсписок - ["Имя", "Значение"])
'''

import crc16
from ctypes import c_int8, c_int32
import threading

# замок для мультипоточного запроса разбора данных
data_lock = threading.Lock()
# раскрашивание переменных
# модули
linking_module = 6
lm_beacon = 0x80
lm_tmi = 0x81


def frame_parcer(frame):
    with data_lock:
        data = []
        while len(frame) < 64:
            frame.append(0xFEFE)
            pass
        if 0x0FF1 == _rev16(frame[0]):  # проверка на метку кадра
            if get_id_loc_data(_rev16(frame[1]))[0] == linking_module:
                if get_id_loc_data(_rev16(frame[1]))[2] == lm_beacon:
                    #
                    data.append(["Метка кадра", "0x%04X" % _rev16(frame[0])])
                    data.append(["Определитель", "0x%04X" % _rev16(frame[1])])
                    data.append(["Номер кадра, шт", "%d" % _rev16(frame[2])])
                    data.append(["Время кадра, с", "%d" % _rev32(frame[3], frame[4])])
                    #
                    data.append(["Статус МС", "0x%02X" % ((frame[5] >> 0) & 0xFF)])
                    data.append(["Темп. МС, °С", "%d" % ((frame[5] >> 8) & 0xFF)])
                    data.append(["Стутус ПН", "0x%04X" % _rev16(frame[6])])
                    data.append(["Статус пит. ПН", "0x%02X" % ((frame[7] >> 0) & 0xFF)])
                    #
                    data.append(["CRC-16", "0x%04X" % crc16.calc(frame, 64)])
                elif get_id_loc_data(_rev16(frame[1]))[2] == lm_tmi:
                    #
                    data.append(["Метка кадра", "0x%04X" % _rev16(frame[0])])
                    data.append(["Определитель", "0x%04X" % _rev16(frame[1])])
                    data.append(["Номер кадра, шт", "%d" % _rev16(frame[2])])
                    data.append(["Время кадра, с", "%d" % _rev32(frame[3], frame[4])])
                    #
                    for i in range(6):
                        data.append(["ПН%d статус" % i, "0x%04X" % _rev16(frame[5+i])])
                    for i in range(7):
                        data.append(["ПН%d напр., В" % i, "%.2f" % (((frame[11+i] >> 8) & 0xFF)/(2**4))])
                        data.append(["ПН%d ток, А" % i, "%.2f" % (((frame[11+i] >> 0) & 0xFF)/(2**4))])
                    data.append(["МС темп.,°С", "%.2f" % ((frame[18] >> 8) & 0xFF)])
                    data.append(["ПН1 темп.,°С", "%.2f" % ((frame[18] >> 0) & 0xFF)])
                    data.append(["ПН2 темп.,°С", "%.2f" % ((frame[19] >> 8) & 0xFF)])
                    data.append(["ПН3 темп.,°С", "%.2f" % ((frame[19] >> 0) & 0xFF)])
                    data.append(["ПН4 темп.,°С", "%.2f" % ((frame[20] >> 8) & 0xFF)])
                    #
                    data.append(["Статус пит. ПН", "0x%02X" % ((frame[20] >> 0) & 0xFF)])
                    data.append(["Память ИСС, %", "%.1f" % (100*((frame[21] >> 8) & 0xFF)/256)])
                    data.append(["Память ДКР, %", "%.1f" % (100*((frame[21] >> 0) & 0xFF)/256)])
                    data.append(["Счетчик включений", "%d" % ((frame[22] >> 8) & 0xFF)])
                    data.append(["Выравнивание", "0x%02X" % ((frame[22] >> 0) & 0xFF)])
                    #
                    data.append(["CRC-16", "0x%04X" % crc16.calc(frame, 64)])
                else:
                    data.append(["Неизвестный тип данных", "0"])
            else:
                data.append(["Неизвестный определитель", "0"])
        else:
            data.append(["Данные не распознаны", "0"])
        return data


def get_id_loc_data(id_loc):
    device_id = (id_loc >> 12) & 0xF
    flags = (id_loc >> 8) & 0xF
    data_id = (id_loc >> 0) & 0xFF
    return device_id, flags, data_id


def _rev16(var):
    return ((var & 0xFF00) >> 8) + ((var & 0xFF) << 8)


def _rev32(var1, var2):
    return ((((var2 & 0xFF00) >> 8) + ((var2 & 0xFF) << 8)) << 16) + ((var1 & 0xFF00) >> 8) + ((var1 & 0xFF) << 8)


