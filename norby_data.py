
#    модуль собирающий в себе стандартизованные функции разбора данных
#    Стандарт:
#    параметры:
#        frame - побайтовый листа данных
#    возвращает:
#        table_list - список подсписков (подсписок - ["Имя", "Значение"]) - оба поля текстовые

import threading

# замок для мультипоточного запроса разбора данных
data_lock = threading.Lock()
# раскрашивание переменных
# модули
linking_module = 6
# тип кадров
lm_beacon = 0x80
lm_tmi = 0x81
lm_full_tmi = 0x82
lm_cyclogram_result = 0x89
lm_load_param = 0x8A


def frame_parcer(frame):
    try:
        with data_lock:
            data = []
            #
            while len(frame) < 128:
                frame.append(0xFE)
            #
            try:
                b_frame = bytes(frame)
            except Exception as error:
                print(error)
            if 0x0FF1 == val_from(frame, 0, 2):  # проверка на метку кадра
                if get_id_loc_data(val_from(frame, 2, 2))["dev_id"] == linking_module:
                    if get_id_loc_data(val_from(frame, 2, 2))["data_code"] == lm_beacon:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 4, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 6, 4)])
                        #
                        data.append(["Статус МС", "0x%02X" % val_from(frame, 10, 2)])
                        data.append(["Стутус ПН", "0x%04X" % val_from(frame, 12, 2)])
                        data.append(["Темп. МС, °С", "%d" % val_from(frame, 14, 1, signed=True)])
                        data.append(["Статус пит. ПН", "0x%02X" % val_from(frame, 15, 1)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    elif get_id_loc_data(val_from(frame, 2, 2))["data_code"] == lm_tmi:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 4, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 6, 4)])
                        #
                        for i in range(6):
                            data.append(["ПН%d статус" % i, "0x%04X" % val_from(frame, (10 + i * 2), 2)])
                        for i in range(7):
                            data.append(["ПН%d напр., В" % i, "%.2f" % (val_from(frame, (22 + i * 2), 1) / (2 ** 4))])
                            data.append(["ПН%d ток, А" % i, "%.2f" % (val_from(frame, (23 + i * 2), 1) / (2 ** 4))])
                        data.append(["МС темп.,°С", "%.2f" % val_from(frame, 36, 1, signed=True)])
                        data.append(["ПН1 темп.,°С", "%.2f" % val_from(frame, 37, 1, signed=True)])
                        data.append(["ПН2 темп.,°С", "%.2f" % val_from(frame, 38, 1, signed=True)])
                        data.append(["ПН3 темп.,°С", "%.2f" % val_from(frame, 39, 1, signed=True)])
                        data.append(["ПН4 темп.,°С", "%.2f" % val_from(frame, 40, 1, signed=True)])
                        #
                        data.append(["Статус пит. ПН", "0x%02X" % val_from(frame, 41, 1)])
                        data.append(["Память ИСС, %", "%.1f" % val_from(frame, 42, 1)])
                        data.append(["Память ДКР, %", "%.1f" % val_from(frame, 43, 1)])
                        data.append(["Счетчик включений", "%d" % val_from(frame, 44, 1)])
                        data.append(["К.Р. питаиня", "0x%02X" % val_from(frame, 45, 1)])
                        data.append(["К.Р. запрет", "0x%02X" % val_from(frame, 46, 2)])
                        data.append(["Память ИСС у.ч.", "%d" % val_from(frame, 48, 2)])
                        data.append(["Память ИСС у.з.", "%d" % val_from(frame, 50, 2)])
                        data.append(["Память ИСС объем.", "%d" % val_from(frame, 52, 2)])
                        data.append(["Память ДКР у.ч.", "%d" % val_from(frame, 54, 2)])
                        data.append(["Память ДКР у.з.", "%d" % val_from(frame, 56, 2)])
                        data.append(["Память ДКР объем", "%d" % val_from(frame, 58, 2)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    elif get_id_loc_data(val_from(frame, 2, 2))["data_code"] == lm_full_tmi:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 4, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 6, 4)])
                        #
                        data.append(["LM:status", "0x%04X" % val_from(frame, 10, 2)])
                        data.append(["LM:err.flgs", "0x%04X" % val_from(frame, 12, 2)])
                        data.append(["LM:err.cnt", "%d" % val_from(frame, 14, 1)])
                        data.append(["LM:rst.cnt", "%d" % val_from(frame, 15, 1)])
                        data.append(["LM:U,V", "%.3f" % (val_from(frame, 16, 2) / 256)])
                        data.append(["LM:I,A", "%.3f" % (val_from(frame, 18, 2) / 256)])
                        data.append(["LM:T,°C", "%.3f" % (val_from(frame, 20, 2) / 256)])
                        #
                        for num, suff in enumerate(["A", "B"]):
                            name = "PL11%s" % suff
                            offs = [28, 46][num]
                            #
                            data.append(["%s:status" % name, "0x%04X" % val_from(frame, offs + 0, 2)])
                            data.append(["%s:err.flgs" % name, "0x%04X" % val_from(frame, offs + 2, 2)])
                            data.append(["%s:err.cnt" % name, "%d" % val_from(frame, offs + 4, 1)])
                            data.append(["%s:inhibits" % name, "%02X" % val_from(frame, offs + 5, 1)])
                            data.append(["%s:U,V" % name, "%.3f" % (val_from(frame, offs + 6, 2, signed=True) / 256)])
                            data.append(["%s:I,A" % name, "%.3f" % (val_from(frame, offs + 8, 2, signed=True) / 256)])
                            data.append(["%s:T,°C" % name, "%.3f" % (val_from(frame, offs + 10, 2, signed=True) / 256)])
                            #
                            stm = val_from(frame, offs + 13, 1)
                            data.append(["%s:STM_INT" % name, "0x%02X" % ((stm >> 0) & 0x01)])
                            data.append(["%s:STM_PWR_ERR" % name, "0x%02X" % ((stm >> 1) & 0x01)])
                            data.append(["%s:STM_WD" % name, "0x%02X" % ((stm >> 2) & 0x01)])
                            data.append(["%s:STM_CPU_ERR" % name, "0x%02X" % ((stm >> 3) & 0x01)])
                            #
                            iku = val_from(frame, offs + 12, 1)
                            data.append(["%s:IKU_RST_FPGA" % name, "0x%02X" % ((iku >> 0) & 0x01)])
                            data.append(["%s:IKU_RST_LEON" % name, "0x%02X" % ((iku >> 1) & 0x01)])
                        #
                        name = "PL12"
                        offs = 64
                        data.append(["%s:status" % name, "0x%04X" % val_from(frame, offs + 0, 2)])
                        data.append(["%s:err.flgs" % name, "0x%04X" % val_from(frame, offs + 2, 2)])
                        data.append(["%s:err.cnt" % name, "%d" % val_from(frame, offs + 4, 1)])
                        data.append(["%s:inhibits" % name, "%02X" % val_from(frame, offs + 5, 1)])
                        data.append(["%s:U,V" % name, "%.3f" % (val_from(frame, offs + 6, 2, signed=True) / 256)])
                        data.append(["%s:I,A" % name, "%.3f" % (val_from(frame, offs + 8, 2, signed=True) / 256)])
                        data.append(["%s:T,°C" % name, "%.3f" % (val_from(frame, offs + 10, 2, signed=True) / 256)])
                        #
                        stm = val_from(frame, offs + 13, 1)
                        data.append(["%s:TM_PWR_ERR" % name, "0x%02X" % ((stm >> 0) & 0x01)])
                        data.append(["%s:TM_CPU_OK" % name, "0x%02X" % ((stm >> 1) & 0x01)])
                        data.append(["%s:TM_INT" % name, "0x%02X" % ((stm >> 2) & 0x01)])
                        data.append(["%s:TM_ERR" % name, "0x%02X" % ((stm >> 3) & 0x01)])
                        #
                        iku = val_from(frame, offs + 12, 1)
                        data.append(["%s:IKU_nRST" % name, "0x%02X" % ((iku >> 0) & 0x01)])
                        data.append(["%s:IKU_SPI_SEL" % name, "0x%02X" % ((iku >> 1) & 0x01)])
                        #
                        name = "PL20"
                        offs = 82
                        data.append(["%s:status" % name, "0x%04X" % val_from(frame, offs + 0, 2)])
                        data.append(["%s:err.flgs" % name, "0x%04X" % val_from(frame, offs + 2, 2)])
                        data.append(["%s:err.cnt" % name, "%d" % val_from(frame, offs + 4, 1)])
                        data.append(["%s:inhibits" % name, "%02X" % val_from(frame, offs + 5, 1)])
                        data.append(["%s:U,V" % name, "%.3f" % (val_from(frame, offs + 6, 2, signed=True) / 256)])
                        data.append(["%s:I,A" % name, "%.3f" % (val_from(frame, offs + 8, 2, signed=True) / 256)])
                        data.append(["%s:T,°C" % name, "%.3f" % (val_from(frame, offs + 10, 2, signed=True) / 256)])
                        #
                        stm = val_from(frame, offs + 13, 1)
                        data.append(["%s:TM_SYS_FAIL" % name, "0x%02X" % ((stm >> 0) & 0x01)])
                        data.append(["%s:TM_I_MON" % name, "0x%02X" % ((stm >> 1) & 0x01)])
                        data.append(["%s:TM_INT" % name, "0x%02X" % ((stm >> 2) & 0x01)])
                        data.append(["%s:TM_ANA" % name, "0x%02X" % ((stm >> 3) & 0x01)])
                        #
                        iku = val_from(frame, offs + 12, 1)
                        data.append(["%s:IKU_EXT_RST" % name, "0x%02X" % ((iku >> 0) & 0x01)])
                        #
                        data.append(["PL_DCR:status", "0x%04X" % val_from(frame, 100, 2)])
                        data.append(["PL_DCR:err.flgs", "0x%04X" % val_from(frame, 102, 2)])
                        data.append(["PL_DCR:err.cnt", "%d" % val_from(frame, 104, 1)])
                        data.append(["PL_DCR:PWR_SW", "0x%02X" % val_from(frame, 105, 1)])
                        data.append(["PL_DCR:Umcu,V", "%.3f" % (val_from(frame, 106, 2, signed=True) / 256)])
                        data.append(["PL_DCR:Imcu,A", "%.3f" % (val_from(frame, 108, 2, signed=True) / 256)])
                        data.append(["PL_DCR:Umsr,V", "%.3f" % (val_from(frame, 110, 2, signed=True) / 256)])
                        data.append(["PL_DCR:Imsr,A", "%.3f" % (val_from(frame, 112, 2, signed=True) / 256)])
                        data.append(["PL_DCR:rx cnt", "%d" % val_from(frame, 114, 1)])
                        data.append(["PL_DCR:tx cnt", "%d" % val_from(frame, 115, 1)])
                        #
                        data.append(["MEM: ISS wr_ptr", "%d" % val_from(frame, 22, 2)])
                        data.append(["MEM: DCR wr_ptr", "%d" % val_from(frame, 24, 2)])
                        data.append(["MEM: ISS rd_ptr", "%d" % val_from(frame, 118, 2)])
                        data.append(["MEM: ISS vol", "%d" % val_from(frame, 120, 2)])
                        data.append(["MEM: DCR rd_ptr", "%d" % val_from(frame, 122, 2)])
                        data.append(["MEM: DCR vol", "%d" % val_from(frame, 124, 2)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    elif get_id_loc_data(val_from(frame, 2, 2))["data_code"] == lm_cyclogram_result:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 4, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 6, 4)])
                        data.append(["Кол-во кадров, шт.", "%d" % val_from(frame, 10, 2)])
                        #
                        data.append(["№ цикл.", "%d" % val_from(frame, 12, 2)])
                        data.append(["Режим", "0x%02X" % val_from(frame, 14, 1)])
                        data.append(["Статус", "0x%02X" % val_from(frame, 15, 1)])
                        #
                        for num in range(8):
                            sub_offs = num*12 + 30
                            data.append(["ТМИ%d: №" % num, "%d" % val_from(frame, 0 + sub_offs, 1)])
                            data.append([" ТМИ%d: ПН" % num, "0x%04X" % val_from(frame, 1 + sub_offs, 1)])
                            data.append([" ТМИ%d: U,В" % num, "%.2f" % (val_from(frame, 2 + sub_offs, 1)/(2**4))])
                            data.append([" ТМИ%d: I,А" % num, "%.2f" % (val_from(frame, 3 + sub_offs, 1)/(2**4))])
                            data.append([" ТМИ%d: ИКУ" % num, "0x%02X" % val_from(frame, 4 + sub_offs, 1)])
                            data.append([" ТМИ%d: СТМ" % num, "0x%02X" % val_from(frame, 5 + sub_offs, 1)])
                            data.append([" ТМИ%d: °С" % num, "%d" % val_from(frame, 6 + sub_offs, 1, signed=True)])
                            data.append([" ТМИ%d: Счетчик ош." % num, "%d" % val_from(frame, 7 + sub_offs, 1)])
                            data.append([" ТМИ%d: ПН ош." % num, "0x%04X" % val_from(frame, 8 + sub_offs, 1)])
                            data.append([" ТМИ%d: ПН ст." % num, "0x%04X" % val_from(frame, 9 + sub_offs, 1)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    elif get_id_loc_data(val_from(frame, 2, 2))["data_code"] == lm_load_param:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 4, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 6, 4)])
                        #
                        data.append(["Версия", "%d.%02d.%02d" % (val_from(frame, 10, 2),
                                                                 val_from(frame, 12, 2),
                                                                 val_from(frame, 14, 2))])
                        data.append(["К. питания", "%d" % val_from(frame, 16, 2, signed=True)])
                        data.append(["К. темп", "%d" % val_from(frame, 18, 2, signed=True)])
                        data.append(["Циклограммы", "%d" % val_from(frame, 20, 2, signed=True)])
                        data.append(["CAN", "%d" % val_from(frame, 22, 2, signed=True)])
                        data.append(["Внеш. память", "%d" % val_from(frame, 24, 2, signed=True)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    else:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 4, 2)])
                        #
                        data.append(["Неизвестный тип данных", "0"])
                else:
                    #
                    data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                    data.append(["Определитель", "0x%04X" % val_from(frame, 2, 2)])
                    #
                    data.append(["Неизвестный определитель", "0"])
            else:
                data.append(["Данные не распознаны", "0"])
            return data
    except Exception as error:
        print(error)
        return None


def get_id_loc_data(id_loc):
    """
    разбор переменной IdLoc
    :param id_loc: переменная, содржащая IdLoc по формату описания на протокол СМКА
    :return: кортеж значений полей переменной IdLoc: номер устройства, флаги записи, код данных
    """
    device_id = (id_loc >> 12) & 0xF
    flags = (id_loc >> 8) & 0xF
    data_id = (id_loc >> 0) & 0xFF
    return {"dev_id": device_id, "flags": flags, "data_code": data_id}


def val_from(frame, offset, leng, byteorder="little", signed=False, debug=False):
    """
    обертка для функции сбора переменной из оффсета и длины, пишется короче и по умолчанию значения самый используемые
    :param frame: лист с данными кадра
    :param offset: оффсет переменной в байтах
    :param leng: длина переменной в байтах
    :param byteorder: порядок следования байт в срезе ('little', 'big')
    :param signed: знаковая или не знаковая переменная (True, False)
    :return: интовое значение переменной
    """
    retval = int.from_bytes(frame[offset + 0:offset + leng], byteorder=byteorder, signed=signed)
    if debug:
        print(frame[offset + 0:offset + leng], " %04X" % int.from_bytes(frame[offset + 0:offset + leng], byteorder=byteorder, signed=signed))
    return retval


# алгоритм подсчета crc16 для кадра
crc16tab = [0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
            0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
            0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
            0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
            0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
            0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
            0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
            0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
            0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
            0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
            0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
            0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
            0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
            0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
            0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
            0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
            0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
            0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
            0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
            0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
            0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
            0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
            0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
            0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
            0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
            0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
            0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
            0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
            0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
            0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
            0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
            0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0]


def crc16_calc(buf, length):
    d = 1
    crc = 0x1D0F
    for i in range(length):
        index = ((crc >> 8) ^ buf[i + d]) & 0x00FF
        crc = (crc << 8) ^ crc16tab[index]
        crc &= 0xFFFF
        d = -d
    return crc
