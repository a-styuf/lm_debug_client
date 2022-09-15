import lm_data
import time
import crc16
import copy
import random

# класс для управления устройством
lm = lm_data.LMData(serial_numbers=["0000ACF00000"], address=6, debug=False)
def get_time():
    return time.strftime("%H-%M-%S", time.localtime()) + "." + ("%.3f: " % time.perf_counter()).split(".")[1]


def pl_pwr_ctrl(pl_num=0, on_off=0):
    lm.read_cmd_reg(mode="lm_pn_pwr_switch", leng=1)
    time.sleep(0.1)
    state = 0
    if lm.com_registers:
        state = lm.com_registers[0]
    if on_off:
        state |= 1 << pl_num
    else:
        state &= ~(1 << pl_num)
    lm.send_cmd_reg(mode="lm_pn_pwr_switch", data=[state])
    time.sleep(0.1)


def pl_pwr_ctrl_all(on_off=0):
    lm.read_cmd_reg(mode="lm_pn_pwr_switch", leng=1)
    time.sleep(0.1)
    if on_off:
        state = 0xFF
    else:
        state = 0x00
    lm.send_cmd_reg(mode="lm_pn_pwr_switch", data=[state])
    time.sleep(0.1)


def get_pwr_info(channel_type="lm"):
    lm.read_tmi(mode="lm_full_tmi")
    time.sleep(2)
    pl_choosing_dict = {"lm": ["LM:U,V", "LM:I,A"],
                        "pl1": ["PL11A:U,V", "PL11A:I,A"],
                        "pl2": ["PL11B:U,V", "PL11B:I,A"],
                        "pl3": ["PL12:U,V", "PL12:I,A"],
                        "pl4": ["PL20:U,V", "PL20:I,A"],
                        "pl5_1": ["PL_DCR:Umcu,V", "PL_DCR:Imcu,A"],
                        "pl5_2": ["PL_DCR:Umsr,V", "PL_DCR:Imsr,A"]
                        }
    voltage = lm.tmi_dict.get(pl_choosing_dict[channel_type][0], 0.0)
    current = lm.tmi_dict.get(pl_choosing_dict[channel_type][1], 0.0)
    return voltage, current


def mb_answer(ad=0x05, fc=0x03, ar=0x0001, lr=0x01, dr=0x00, dl=None):
    data_to_send = []
    if fc == 0x03:  # F3
        data_to_send = [ad, fc, lr*2]
        data_to_send.extend(dl)
    elif fc == 0x06:  # F6
        data_to_send = [ad, fc, (ar >> 8) & 0xFF, (ar >> 0) & 0xFF, (dr >> 8) & 0xFF, (dr >> 0) & 0xFF]
    elif fc == 0x10:  # F16
        data_to_send = [ad, fc, (ar >> 8) & 0xFF, (ar >> 0) & 0xFF, 0x00, lr]
    crc16_reg = crc16.calc_modbus_crc16_bytes(data_to_send)
    data_to_send.extend(crc16_reg)
    return data_to_send


def mb_request(ad=0x05, fc=0x03, ar=0x0001, lr=0x01, dr=0x00, dl=None):
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
    return data_to_send


def pl_send_instamessage(pl_num=1, data=[], debug=True):
    can_data = [0 for i in range(128)]
    req_param_dict = {"can_num": 0,
                      "dev_id": lm.address, "mode": "write", "var_id": 8, "offset": 0, "d_len": 128, "data": can_data}
    req_param_dict["data"][0] = pl_num
    req_param_dict["data"][127] = len(data)
    req_param_dict["data"][1:1+len(data)] = data

    id_var = lm.usb_can.request(**req_param_dict)
    if debug:
        print("\tTX: ", lm.usb_can.can_log_str(id_var, req_param_dict["data"][1:len(data)+1], len(data)))
    time.sleep(1)
    req_param_dict = {"can_num": 0, "dev_id": lm.address, "mode": "read", "var_id": 5, "offset": 0, "d_len": 128, "data": []}
    pl_offset = [0, 768, 896, 1024, 1152, 640]
    req_param_dict["offset"] = pl_offset[pl_num]
    id_var = lm.usb_can.request(**req_param_dict)
    time.sleep(1)
    rx_len = lm.instamessage_data[127]
    if debug:
        print("\tRX: ", lm.usb_can.can_log_str(id_var, lm.instamessage_data[0:rx_len], rx_len-1))
    time.sleep(1)
    return lm.instamessage_data[0:rx_len]


def pl_send_instamessage_fake(pl_num=1, data=[], data_rx=[], debug=True):
    can_data = [0 for i in range(128)]
    req_param_dict = {"can_num": 0,
                      "dev_id": lm.address, "mode": "write", "var_id": 8, "offset": 0, "d_len": 128, "data": can_data}
    req_param_dict["data"][0] = pl_num
    req_param_dict["data"][127] = len(data)
    req_param_dict["data"][1:1+len(data)] = data

    id_var = lm.usb_can.request(**req_param_dict)
    if debug:
        print("\tTX: ", lm.usb_can.can_log_str(id_var, req_param_dict["data"][1:len(data)+1], len(data)))
    time.sleep(1)
    req_param_dict = {"can_num": 0, "dev_id": lm.address, "mode": "read", "var_id": 5, "offset": 0, "d_len": 128, "data": []}
    pl_offset = [0, 768, 896, 1024, 1152, 640]
    req_param_dict["offset"] = pl_offset[pl_num]
    id_var = lm.usb_can.request(**req_param_dict)
    time.sleep(1)
    rx_data = data_rx
    rx_len = len(rx_data)
    if debug:
        print("\tRX: ", lm.usb_can.can_log_str(id_var, rx_data, rx_len))
    time.sleep(1)
    return lm.instamessage_data[0:rx_len]


def ekkd_test():
    print(get_time(), "Работа с ПН ККД")
    time.sleep(1)
    print("\t", get_time(), "Включение ККД")
    pl_pwr_ctrl(pl_num=1, on_off=1)
    time.sleep(1)
    for i in range(1):
        print("\t", get_time(), "Запрос данных ККД")
        pl_send_instamessage(pl_num=1, data=mb_request(ad=10, fc=3, ar=0x07D0, lr=2))
        time.sleep(1)
    time.sleep(1)
    pl_pwr_ctrl_all(on_off=0)
    pass


def ekkd_autonomus_test():
    print(get_time(), "Автономные испытания ЭО ККД")
    time.sleep(1)
    print("\t", get_time(), "Включение ККД")
    pl_pwr_ctrl(pl_num=1, on_off=1)
    time.sleep(10)
    voltage, current = get_pwr_info(channel_type="pl1")
    print("\t", get_time(), f"Параметры питания: U {voltage:.1f}V, I {current:.3f}A")
    time.sleep(1)
    for i in range(9):
        print("\t", get_time(), f"Запрос данных №{i} ЭО ККД")
        value = random.randint(50, 200)
        pl_send_instamessage_fake(pl_num=1,
                                  data=mb_request(ad=10, fc=3, ar=0x07D0+2*i, lr=2),
                                  data_rx=mb_answer(ad=10, fc=3, ar=0x07D0+2*i, lr=2, dl=[0x00, 0x00,
                                                                                          (value >> 8) & 0xFF,
                                                                                          value & 0xFF]))
        time.sleep(1)
    time.sleep(1)
    print("\t", get_time(), f"Включение режима констант ЭО ККД")
    pl_send_instamessage_fake(pl_num=1,
                              data=mb_request(ad=10, fc=6, ar=0x07E4, lr=1, dl=[0x00, 0x01]),
                              data_rx=mb_answer(ad=10, fc=6, ar=0x07E4, lr=1))
    time.sleep(1)
    print("\t", get_time(), f"Запрос данных 9-ти датчиков ЭО ККД")
    val_list = [i for i in range(18)]
    pl_send_instamessage_fake(pl_num=1,
                              data=mb_request(ad=10, fc=3, ar=0x07D0 + 2 * i, lr=18),
                              data_rx=mb_answer(ad=10, fc=3, ar=0x07D0 + 2 * i, lr=18, dl=val_list))
    time.sleep(1)
    print("\t", get_time(), f"Отключение режима констант ЭО ККД")
    pl_send_instamessage_fake(pl_num=1,
                              data=mb_request(ad=10, fc=6, ar=0x07E4, lr=1, dl=[0x00, 0x00]),
                              data_rx=mb_answer(ad=10, fc=6, ar=0x07E4, lr=1))
    time.sleep(1)
    print("\t", get_time(), f"Запрос данных 9-ти датчиков ЭО ККД")
    val_list = [random.randint(50, 200) for i in range(18)]
    pl_send_instamessage_fake(pl_num=1,
                              data=mb_request(ad=10, fc=3, ar=0x07D0+2*i, lr=2*9),
                              data_rx=mb_answer(ad=10, fc=3, ar=0x07D0+2*i, lr=2*9, dl=val_list))
    time.sleep(1)
    pl_pwr_ctrl_all(on_off=0)
    print(get_time(), "Автономные испытания ЭО ККД закончены")
    pass


def aznv_autonomus_test():
    print(get_time(), "Автономные испытания АЗНВ")
    time.sleep(1)
    print("\t", get_time(), "Включение АЗНВ")
    pl_pwr_ctrl(pl_num=2, on_off=1)
    time.sleep(15)
    voltage, current = get_pwr_info(channel_type="pl2")
    print("\t", get_time(), f"Параметры питания: U {voltage:.1f}V, I {current:.3f}A")
    for i in range(1):
        #
        print("\n\t", get_time(), "___Проверка чтения регистров___\n")
        print("\t", get_time(), "Запрос Регулярной телеметрии")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0, lr=4))
        time.sleep(1)
        print("\t", get_time(), "Запрос Основной телеметрии")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=4, lr=28))
        time.sleep(1)
        print("\t", get_time(), "Запрос Дополнительной телеметрии")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0x20, lr=32))
        time.sleep(1)
        print("\t", get_time(), f"Запрос Целевой информации (самое старое сообщение АЗНВ)")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0x40, lr=11))
        time.sleep(1)
        #
        print("\n\t", get_time(), "___Проверка записи регистров___\n")
        print("\t", get_time(), "Запись регистра состояния")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=6, ar=0, lr=1, dl=[0xFF, 0xFF]))
        time.sleep(1)
        print("\t", get_time(), "Запрос Основной телеметрии")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=4, lr=28))
        time.sleep(1)
        print("\t", get_time(), "Запись регистров маски")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=16, ar=1, lr=2, dl=[0xAA, 0x55, 0xFF, 0x00]))
        time.sleep(1)
        print("\t", get_time(), "Запрос Основной телеметрии")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=4, lr=28))
        time.sleep(1)
        print("\t", get_time(), "Запись регистров времени")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=16, ar=0, lr=3, dl=[0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF]))
        time.sleep(1)
        print("\t", get_time(), "Запрос Основной телеметрии")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=4, lr=28))
        #
        print("\n\t", get_time(), "___Перезагрузка АЗНВ для сброса параметров в значения по умолчанию___\n")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=6, ar=6, lr=1, dl=[0x3E, 0x3F]))
        time.sleep(15)
        #
        print("\n\t", get_time(), "___Проверка приема сообщений АЗНВ___\n")
        print("\t", get_time(), "Запрос регулярной телеметрии раз в ~10 секунд до появления сообщений")
        msg_num = 0
        while msg_num == 0:
            msg = pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0, lr=4), debug=False)
            msg_num = (msg[3] << 8) + msg[4]
            if msg_num:
                pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0, lr=4))
            time.sleep(10)
        print("\t", get_time(), f"Запрос Целевой информации (самое старое сообщение АЗНВ)")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0x40, lr=11))
        time.sleep(1)
    time.sleep(1)
    pl_pwr_ctrl_all(on_off=0)
    print("\n", get_time(), "Автономные испытания АЗНВ окончены", "\n")
    pass


def aznv_test():
    print(get_time(), "Работа с АЗНВ")
    time.sleep(1)
    print("\t", get_time(), "Включение АЗНВ")
    pl_pwr_ctrl(pl_num=2, on_off=1)
    time.sleep(15)
    for i in range(1):
        print("\t", get_time(), "Запрос Температуры ВИП и платы")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0, lr=4))
        time.sleep(1)
        print("\t", get_time(), "Запрос самого старого сообщения АЗНВ")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=64, lr=11))
        time.sleep(1)
        print("\t", get_time(), "Запись параметров времени")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=16, ar=3, lr=3, dl=[0xAA, 0xBB, 0xCC, 0xDD, 0xCC, 0xEE]))
        time.sleep(1)
    time.sleep(1)
    pl_pwr_ctrl_all(on_off=0)
    pass


def telescope_test():
    print(get_time(), "Работа с Телескоп")
    time.sleep(1)
    print("\t", get_time(), "Включение Телескоп")
    pl_pwr_ctrl(pl_num=4, on_off=1)
    time.sleep(3)
    for i in range(100):
        print("\t", get_time(), "Reset command")
        pl_send_instamessage(pl_num=5, data=[0x56, 0x00, 0x26, 0x00])
        time.sleep(1)
    time.sleep(1)
    pl_pwr_ctrl_all(on_off=0)
    pass


def telescope_autonomus_test():
    print(get_time(), "Работа с ГФО")
    time.sleep(1)
    print("\t", get_time(), "Включение ГФО")
    pl_pwr_ctrl(pl_num=4, on_off=1)
    time.sleep(3)
    voltage, current = get_pwr_info(channel_type="pl4")
    print("\t", get_time(), f"Параметры питания: U {voltage:.1f}V, I {current:.3f}A")
    time.sleep(3)
    print("\t", get_time(), "Stop current frame")
    pl_send_instamessage(pl_num=5, data=[0x56, 0x00, 0x36, 0x01, 00])
    time.sleep(3)
    print("\t", get_time(), "Frame length request")
    data = pl_send_instamessage(pl_num=5, data=[0x56, 0x00, 0x34, 0x01, 00])
    frame_size = int.from_bytes(bytes(data[5:5+4]), 'big')
    time.sleep(1)
    print("\t", get_time(), "Frame request (first 32 bytes)")
    pl_send_instamessage(pl_num=5, data=[0x56, 0x00, 0x32, 0x0C, 0x00, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20, 0x00, 0x64])
    time.sleep(1)
    print("\t", get_time(), "Back to normal operation mode")
    pl_send_instamessage(pl_num=5, data=[0x56, 0x00, 0x36, 0x01, 0x03])
    time.sleep(1)
    pl_pwr_ctrl_all(on_off=0)
    print(get_time(), "Конец работы с ГФО")
    pass


print(get_time(), "Начало работы")
lm.usb_can.reconnect()
while lm.usb_can.state != 1:
    print(get_time(), "Попытка переподключения")
    time.sleep(1)
    lm.usb_can.reconnect()
#general
time.sleep(1)
print(get_time(), "Общее отключение питания")
pl_pwr_ctrl_all(on_off=0)
# ekkd
# aznv
# telescope
ekkd_autonomus_test()

