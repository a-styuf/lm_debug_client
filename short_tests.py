import lm_data
import time


def get_time():
    return time.strftime("%H-%M-%S", time.localtime()) + "." + ("%.3f: " % time.perf_counter()).split(".")[1]


# класс для управления устройством
lm = lm_data.LMData(serial_numbers=["205135995748"], debug=False)

print(get_time(), "Начало работы")
lm.serial.reconnect()
while lm.serial.state != 1:
    print(get_time(), "Попытка переподключения")
    time.sleep(1)
    lm.serial.reconnect()
# тесты
pwr_ch_num = 0x05

while 1:
    while lm.serial.state != 1:
        print(get_time(), "Попытка переподключения")
        time.sleep(1)
        lm.serial.reconnect()
    time.sleep(1)
    print(get_time(), "Отключение каналов ПН1.1")
    lm.send_cmd(mode="pwr_on_off_separately", data=[pwr_ch_num, 0x00])
    time.sleep(1)
    print(get_time(), "Включение e-Fuse 1")
    lm.send_cmd(mode="pwr_on_off_separately", data=[pwr_ch_num, 0x01])
    time.sleep(1)
    print(get_time(), "Отключение каналов ПН1.1")
    lm.send_cmd(mode="pwr_on_off_separately", data=[pwr_ch_num, 0x00])
    time.sleep(1)
    print(get_time(), "Включение e-Fuse 2")
    lm.send_cmd(mode="pwr_on_off_separately", data=[pwr_ch_num, 0x02])
    time.sleep(1)
    print(get_time(), "Отключение каналов ПН1.1")
    lm.send_cmd(mode="pwr_on_off_separately", data=[pwr_ch_num, 0x00])
    time.sleep(1)
    print(get_time(), "Включение преобразователя")
    lm.send_cmd(mode="pwr_on_off_separately", data=[pwr_ch_num, 0x07])
    time.sleep(1)
    print(get_time(), "Отключение каналов ПН1.1")
    lm.send_cmd(mode="pwr_on_off_separately", data=[pwr_ch_num, 0x00])
    pass
