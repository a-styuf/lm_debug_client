import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
import main_win
import lm_data
import time
import os
import data_vis
import can_unit
import pay_load
import cyclogram_result

version = "0.14.3"


class MainWindow(QtWidgets.QMainWindow, main_win.Ui_MainWindow):
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле main_win.py
        #
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.setWindowTitle("Norby - Linking Module. Version {:s}".format(version))
        # класс для управления устройством
        self.lm = lm_data.LMData(serial_numbers=["0000ACF0", "205135995748", "205B359A", "2056359A", "2059359A", "365938753038", "365638633038", "365638633038"], debug=True, address=6)
        self.connectionPButt.clicked.connect(self.lm.usb_can.reconnect)
        # таб с кан-терминалом
        self.can_usb_client_widget = can_unit.ClientGUIWindow(self, interface=self.lm.usb_can)
        self.canTerminalVBLayout = QtWidgets.QVBoxLayout()
        self.canTerminalTab.setLayout(self.canTerminalVBLayout)
        self.canTerminalVBLayout.addWidget(self.can_usb_client_widget)
        # второе окно с графиками
        self.graph_window = data_vis.Widget()
        self.graph_window.restart_graph_signal.connect(self.restart_graph)
        self.openGraphPButton.clicked.connect(self.open_graph_window)
        # управление питанием МС
        self.pwrChsSetPButton.clicked.connect(self.pwr_set_channels_state)
        #
        self.get_general_data_inh = 0  # переменая для запрета опроса на момент других опросов
        self.genDataGetPButton.clicked.connect(self.get_general_data)
        self.cycleReadGenDataPButton.clicked.connect(self.cycle_get_general_data)
        self.genDataReadTimer = QtCore.QTimer()
        self.genDataReadTimer.timeout.connect(self.get_general_data)
        #
        self.allChannelsChBox.clicked.connect(self.pwr_all_channel_choice)
        self.pwr_channels_list = [self.lmChannelsChBox, self.pl11aChannelsChBox, self.pl11bChannelsChBox,
                                  self.pl12ChannelsChBox, self.pl20ChannelsChBox, self.dcr1ChannelsChBox,
                                  self.dcr2ChannelsChBox]
        # режим констант
        self.constModeOnPButton.clicked.connect(self.constant_mode_on)
        self.constModeOffPButton.clicked.connect(self.constant_mode_off)
        # работа с циклограммами
        self.singleCyclPButton.clicked.connect(self.single_cyclogram)
        self.startCyclsPButton.clicked.connect(self.start_cyclograms)
        self.stopCyclsPButton.clicked.connect(self.stop_cyclograms)
        self.readCyclResPButton.clicked.connect(self.read_cyclogram_result)
        self.readCyclResTimer = QtCore.QTimer()
        self.readCyclResCounter = 0

        self.softCyclicModePButton.clicked.connect(self.start_soft_cyclogram)
        self.soft_clg_mode = 0
        self.soft_clg_num = 0
        self.soft_cyclograms = [1, 2, 5]
        self.softCyclTimer = QtCore.QTimer()
        self.softCyclTimer.timeout.connect(self.soft_cyclogram_body)
        # окно с результатом циклограммы
        self.cycl_result_win = cyclogram_result.Widget()
        # работа с ДеКоР
        self.singlDCRDefModePButton.clicked.connect(self.set_dcr_single_mode_default)
        self.cyclicDCRDefModePButton.clicked.connect(self.set_dcr_cyclic_mode_default)
        self.singlDCRFT1ModePButton.clicked.connect(self.set_dcr_single_mode_flight_task_1)
        self.cyclicDCRFT1ModePButton.clicked.connect(self.set_dcr_cyclic_mode_flight_task_1)
        self.singlDCRFT2ModePButton.clicked.connect(self.set_dcr_single_mode_flight_task_2)
        self.cyclicDCRFT2ModePButton.clicked.connect(self.set_dcr_cyclic_mode_flight_task_2)
        self.sendFlTaskPButton.clicked.connect(self.send_fl_task_start)
        self.DCRModePausePButton.clicked.connect(self.set_dcr_mode_pause)
        self.DCRModeOffPButton.clicked.connect(self.set_dcr_mode_off)
        self.DCRFlightTaskTimer = QtCore.QTimer()
        self.DCRFlightTaskCounter = 0
        self.fl_task_1 = []
        self.fl_task_2 = []

        self.writeFlTaskPButton.clicked.connect(self.cmd_write_fl_task)

        # работа с ПН1.1А
        self.pl11a = pay_load.PayLoad(self, lm=self.lm, pl_type="pl11_a")
        self.pl11a.instamessage_signal.connect(self.pl11a_read_word_slot)
        self.pl11AWrPButton.clicked.connect(self.pl11a_write_word)
        self.pl11ARdPButton.clicked.connect(self.pl11a_read_word)
        self.pl11ASetIKUPButton.clicked.connect(self.pl11a_set_iku)
        # работа с ПН1.1Б
        self.pl11b = pay_load.PayLoad(self, lm=self.lm, pl_type="pl11_b")
        self.pl11b.instamessage_signal.connect(self.pl11b_read_word_slot)
        self.pl11BWrPButton.clicked.connect(self.pl11b_write_word)
        self.pl11BRdPButton.clicked.connect(self.pl11b_read_word)
        self.pl11BSetIKUPButton.clicked.connect(self.pl11b_set_iku)
        # работа с ПН1.2
        self.pl12 = pay_load.PayLoad(self, lm=self.lm, pl_type="pl12")
        self.pl12.instamessage_signal.connect(self.pl12_read_word_slot)
        self.pl12WrPButton_2.clicked.connect(self.pl12_write_word)
        self.pl12RdPButton_2.clicked.connect(self.pl12_read_word)
        self.pl12SetIKUPButton_2.clicked.connect(self.pl12_set_iku)
        # работа с ПН1.2
        self.pl20 = pay_load.PayLoad(self, lm=self.lm, pl_type="pl20")
        self.pl20.instamessage_signal.connect(self.pl20_read_word_slot)
        self.pl20RdPButton.clicked.connect(self.pl20_read_word)
        self.pl20SetIKUPButton.clicked.connect(self.pl20_set_iku)
        # общие функции
        self.initLMPButton.clicked.connect(self.init_lm)
        self.formatISSMemPButton.clicked.connect(self.format_iss_mem)
        self.formatDCRMemPButton.clicked.connect(self.format_dcr_mem)
        self.synchLMTimePButton.clicked.connect(self.synch_lm_time)
        self.softResetPButton.clicked.connect(self.soft_reset)
        # работа с памятью
        self.mem_data = ""
        self.mem_retry_cnt= 5
        self.rdPtrAllMemPButton.clicked.connect(self.set_all_mem_rd_ptr)
        self.rdPtrISSMemPButton.clicked.connect(self.set_iss_mem_rd_ptr)
        self.rdPtrDCRMemPButton.clicked.connect(self.set_dcr_mem_rd_ptr)
        self.readFullISSMemPButton.clicked.connect(self.start_full_iss_mem)
        self.stopReadFullISSMemPButton.clicked.connect(self.stop_full_iss_mem)
        self.readFullISSMemTimer = QtCore.QTimer()
        self.readFullDCRMemPButton.clicked.connect(self.start_full_dcr_mem)
        self.stopReadFullDCRMemPButton.clicked.connect(self.stop_full_dcr_mem)
        self.readFullDCRMemTimer = QtCore.QTimer()
        # обновление gui
        self.DataUpdateTimer = QtCore.QTimer()
        self.DataUpdateTimer.timeout.connect(self.update_ui)
        self.DataUpdateTimer.start(1000)
        # логи
        self.data_log_file = None
        self.data_log_file_title = None
        self.cycl_res_log_file = None
        self.iss_mem_log_file = None
        self.dcr_mem_log_file = None
        self.log_str = ""

        self.logRestartPButt.clicked.connect(self.recreate_log_files)
        self.recreate_log_files()

        # UI #
    def update_ui(self):
        try:
            # отрисовка графика
            pass
            # логи
            if self.lm.get_log_file_title() is not None and self.data_log_file_title is None:
                self.data_log_file_title = self.lm.get_log_file_title()
                self.data_log_file.write(self.data_log_file_title)
            elif self.data_log_file_title:
                log_str_tmp = self.lm.get_log_file_data()
                if len(log_str_tmp) < 10:
                    pass
                elif self.log_str == log_str_tmp:
                    pass
                else:
                    self.log_str = log_str_tmp
                    self.data_log_file.write(self.log_str.replace(".", ","))
            # отображение состояния подключения
            self.statusLEdit.setText(self.lm.usb_can.state_string[self.lm.usb_can.state])
            # передача данных в графики
            self.graph_window.set_graph_data(self.lm.general_data)
        except Exception as error:
            print("update_ui: " + str(error))

    def open_graph_window(self):
        if self.graph_window.isVisible():
            self.graph_window.close()
        elif self.graph_window.isHidden():
            self.graph_window.show()
        pass

    # управление питанием
    def pwr_all_channel_choice(self):
        if self.allChannelsChBox.isChecked():
            for channel_ChBox in self.pwr_channels_list:
                channel_ChBox.setChecked(True)
        else:
            for channel_ChBox in self.pwr_channels_list:
                channel_ChBox.setChecked(False)
        pass

    def pwr_set_channels_state(self):
        channel_state = 0x00
        for num, channel_ChBox in enumerate(self.pwr_channels_list):
            if channel_ChBox.isChecked():
                channel_state |= 1 << num
        self.lm.send_cmd_reg(mode="lm_pn_pwr_switch", data=[channel_state & 0xFF])
        pass

    # constant mode
    def constant_mode_on(self):
        self.lm.send_cmd_reg(mode="const_mode", data=[0x01])
        pass

    def constant_mode_off(self):
        self.lm.send_cmd_reg(mode="const_mode", data=[0x00])
        pass

    # general data_read
    def get_general_data(self):
        if self.get_general_data_inh == 0:
            self.lm.read_tmi(mode="lm_full_tmi")
        pass

    def cycle_get_general_data(self):
        if self.genDataReadTimer.isActive():
            self.genDataReadTimer.stop()
        else:
            self.genDataReadTimer.start(1000)
        pass

    def restart_graph(self):
        self.lm.reset_general_data()
        pass

    # управление циклограммами
    def single_cyclogram(self):
        try:
            cyclogram_num = int(self.singleCyclSBox.value()) & 0xFF
        except ValueError:
            cyclogram_num = 0
            self.singleCyclSBox.setValue(0)
        self.lm.send_cmd_reg(mode="cyclogram_start", data=[0x01, cyclogram_num])
        pass

    def start_cyclograms(self):
        self.lm.send_cmd_reg(mode="cyclogram_start", data=[0x02, 0x00])
        pass

    def stop_cyclograms(self):
        self.lm.send_cmd_reg(mode="cyclogram_start", data=[0x00, 0x00])
        pass

    def read_cyclogram_result(self):
        self.readCyclResTimer.singleShot(50, self.read_cyclogram_result_body)
        self.readCyclResPButton.setEnabled(False)
        pass

    def read_cyclogram_result_body(self):
        if self.readCyclResCounter < 33:
            self.readCyclResTimer.singleShot(300, self.read_cyclogram_result_body)
            self.lm.read_cyclogram_result(self.readCyclResCounter)
            self.readCyclResCounter += 1
        else:
            self.readCyclResPButton.setEnabled(True)
            self.readCyclResCounter = 0
            self.cycl_res_log_file = self.create_log_file(prefix="Cyclogram_Result", sub_sub_dir=False, sub_dir="Cyclogram", extension=".txt")
            self.cycl_res_log_file.write(self.lm.get_cyclogram_result_str())
            self.cycl_res_log_file.write(self.lm.get_parc_cyclogram_result())
            self.cycl_res_log_file.close()
            self.cycl_result_win.show()
            self.cycl_result_win.cyclResultTEdit.setText(self.lm.get_cyclogram_result_str() + self.lm.get_parc_cyclogram_result())

    def start_soft_cyclogram(self):
        if self.softCyclicModePButton.isChecked() is False:
            self.softCyclTimer.stop()
            self.soft_clg_mode = 0
        else:
            self.softCyclTimer.start(1000)
        pass

    def soft_cyclogram_body(self):
        try:
            self.softCyclTimer.setInterval(self.softCyclogramPeriodSBox.value() * 1000)
            #
            if self.soft_clg_mode == 0:
                self.soft_clg_mode = 1
            else:
                self.read_cyclogram_result_body()
            if self.soft_clg_num >= len(self.soft_cyclograms):
                self.soft_clg_num = 0
            cyclogram_num = self.soft_cyclograms[self.soft_clg_num]
            self.soft_clg_num += 1
            self.lm.send_cmd_reg(mode="cyclogram_start", data=[0x01, cyclogram_num])
            print(cyclogram_num)
        except Exception as error:
            print("soft cycl body:", error)
        pass

    # General function #
    def init_lm(self):
        self.lm.send_cmd(mode="lm_init")
        pass

    def format_iss_mem(self):
        self.lm.send_cmd(mode="iss_mem_clear")
        pass

    def format_dcr_mem(self):
        self.lm.send_cmd(mode="dcr_mem_clear")
        pass

    def synch_lm_time(self):
        time_s_from_2000 = time.mktime(time.strptime("2000-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"))
        time_tmp_s = int(time.time() - time_s_from_2000)
        self.lm.send_cmd_reg(mode="synch_time", data=self.get_list_from_int32_val(time_tmp_s))

    def soft_reset(self):
        self.lm.send_cmd_reg(mode="lm_soft_reset", data=[0xA5])
        pass

    # работа с памятью
    def set_all_mem_rd_ptr(self):
        mem_num = 127
        rd_ptr = self.rdPtrAllMemSBox.value()
        data = [mem_num]
        data.extend(self.get_list_from_int32_val(rd_ptr))
        self.lm.send_cmd_reg(mode="part_mem_rd_ptr", data=data)
        pass

    def set_iss_mem_rd_ptr(self):
        mem_num = 0
        rd_ptr = self.rdPtrISSMemSBox.value()
        data = [mem_num]
        data.extend(self.get_list_from_int32_val(rd_ptr))
        self.lm.send_cmd_reg(mode="part_mem_rd_ptr", data=data)
        pass

    def set_dcr_mem_rd_ptr(self):
        mem_num = 1
        rd_ptr = self.rdPtrDCRMemSBox.value()
        data = [mem_num]
        data.extend(self.get_list_from_int32_val(rd_ptr))
        self.lm.send_cmd_reg(mode="part_mem_rd_ptr", data=data)
        pass

    @staticmethod
    def get_list_from_int32_val(val):
        return [((val >> 0) & 0xff), ((val >> 8) & 0xff), ((val >> 16) & 0xff), ((val >> 24) & 0xff)]

    def start_full_iss_mem(self):
        self.readFullISSMemPButton.setEnabled(False)
        self.lm.read_mem(mode="iss_mem")
        self.readFullISSMemTimer.singleShot(1000, self.read_full_iss_mem)
        #
        self.cycl_res_log_file = self.create_log_file(prefix="ISS mem", sub_sub_dir=False, sub_dir="ISS mem",
                                                      extension=".txt")

    def stop_full_iss_mem(self):
        self.mem_data = ""
        self.mem_retry_cnt = 10
        try:
            self.cycl_res_log_file.close()
        except Exception:
            pass
        self.readFullISSMemPButton.setEnabled(True)
        self.readFullISSMemTimer.stop()

    def read_full_iss_mem(self):
        state = 0
        # блок определения состояния
        try:
            mem_data = self.lm.get_mem_data(1)
            if mem_data and (mem_data in self.mem_data):
                if self.mem_retry_cnt > 0:
                    self.mem_retry_cnt -= 1
                    state = 2
                else:
                    state = 0
            else:
                self.mem_retry_cnt = 10
                state = 1
            self.mem_data = mem_data
            print(self.mem_data)
            # блок разборки необходимости действий
            if state == 1:
                self.mem_retry_cnt = 10
                self.lm.read_mem(mode="iss_mem")
                self.cycl_res_log_file.write(mem_data)
                self.readFullISSMemTimer.singleShot(350, self.read_full_iss_mem)
            elif state == 2:
                self.lm.read_mem(mode="iss_mem")
                self.readFullISSMemTimer.singleShot(350, self.read_full_iss_mem)
            elif state == 0:
                self.stop_full_iss_mem()
        except Exception as error:
            self.stop_full_iss_mem()
            print(error)
        pass

    def start_full_dcr_mem(self):
        self.lm.read_mem(mode="dcr_mem")
        self.readFullDCRMemTimer.singleShot(300, self.read_full_dcr_mem)
        #
        self.cycl_res_log_file = self.create_log_file(prefix="DCR mem", sub_sub_dir=False, sub_dir="DCR mem",
                                                      extension=".txt")
        self.readFullDCRMemPButton.setEnabled(False)

    def stop_full_dcr_mem(self):
        self.mem_data = ""
        self.mem_retry_cnt = 20
        try:
            self.cycl_res_log_file.close()
        except Exception:
            pass
        self.readFullDCRMemPButton.setEnabled(True)
        self.readFullDCRMemTimer.stop()

    def read_full_dcr_mem(self):
        state = 0
        # блок определения состояния
        try:
            mem_data = self.lm.get_mem_data(2)
            if mem_data and (mem_data in self.mem_data):
                if self.mem_retry_cnt > 0:
                    self.mem_retry_cnt -= 1
                    state = 2
                else:
                    state = 0
            else:
                self.mem_retry_cnt = 20
                state = 1
            self.mem_data = mem_data
            # блок разборки необходимости действий
            if state == 1:
                self.mem_retry_cnt = 20
                self.lm.read_mem(mode="dcr_mem")
                self.cycl_res_log_file.write(mem_data)
                self.readFullDCRMemTimer.singleShot(300, self.read_full_dcr_mem)
            elif state == 2:
                self.lm.read_mem(mode="dcr_mem")
                self.readFullDCRMemTimer.singleShot(300, self.read_full_dcr_mem)
            elif state == 0:
                self.stop_full_dcr_mem()
        except Exception as error:
            self.stop_full_dcr_mem()
            print(error)
        pass

    # управление ДеКоР
    def set_dcr_single_mode_default(self):
        self.lm.send_cmd_reg(mode="pn_dcr_mode", data=[0x01])
        pass

    def set_dcr_single_mode_flight_task_1(self):
        self.lm.send_cmd_reg(mode="pn_dcr_mode", data=[0x02])
        pass

    def set_dcr_single_mode_flight_task_2(self):
        self.lm.send_cmd_reg(mode="pn_dcr_mode", data=[0x03])
        pass

    def set_dcr_cyclic_mode_default(self):
        self.lm.send_cmd_reg(mode="pn_dcr_mode", data=[0x11])
        pass

    def set_dcr_cyclic_mode_flight_task_1(self):
        self.lm.send_cmd_reg(mode="pn_dcr_mode", data=[0x12])
        pass

    def set_dcr_cyclic_mode_flight_task_2(self):
        self.lm.send_cmd_reg(mode="pn_dcr_mode", data=[0x13])
        pass

    def set_dcr_mode_off(self):
        self.lm.send_cmd_reg(mode="pn_dcr_mode", data=[0x00])
        pass

    def set_dcr_mode_pause(self):
        self.lm.send_cmd_reg(mode="pn_dcr_mode", data=[0x04])
        pass

    def send_fl_task_start(self):
        self.sendFlTaskPButton.setEnabled(False)
        #
        self.DCRFlightTaskCounter += 0
        self.fl_task_1 = []
        self.fl_task_2 = []
        # очистка полетного задания 1
        for i in range(128):
            self.fl_task_1.append(self.create_flight_task_list_step(type=0, cmd=0x00, pause=0, repeat=0, data=None))
        # дозапись полетного задания 1
        self.fl_task_1[0] = self.create_flight_task_list_step(type=1, cmd=0x01, pause=3000, repeat=0, data=[0x03])  # включить питание: МК и ИЗМ
        self.fl_task_1[1] = self.create_flight_task_list_step(type=2, cmd=0x01, pause=1000, repeat=0, data=[0x72, 0xC7, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # отправка команды
        self.fl_task_1[2] = self.create_flight_task_list_step(type=3, cmd=0x00, pause=1000, repeat=0, data=None)  # синхронизация времени
        self.fl_task_1[3] = self.create_flight_task_list_step(type=2, cmd=0x01, pause=1000, repeat=0, data=[0x72, 0xC7, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # отправка команды
        self.fl_task_1[4] = self.create_flight_task_list_step(type=2, cmd=0x01, pause=1000, repeat=0, data=[0x62, 0xD2, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # отправка команды
        self.fl_task_1[5] = self.create_flight_task_list_step(type=2, cmd=0x01, pause=1000, repeat=0, data=[0x72, 0xC7, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # отправка команды
        self.fl_task_1[6] = self.create_flight_task_list_step(type=8, cmd=0x01, pause=60000, repeat=60, data=None)  # пустая команда
        self.fl_task_1[7] = self.create_flight_task_list_step(type=2, cmd=0x01, pause=1000, repeat=0, data=[0x72, 0xC7, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # отправка команды
        self.fl_task_1[8] = self.create_flight_task_list_step(type=2, cmd=0x01, pause=100, repeat=1000, data=[0x72, 0xC3, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # отправка команды
        self.fl_task_1[9] = self.create_flight_task_list_step(type=1, cmd=0x00, pause=0, repeat=0, data=[0x03]) # выключить питание:  МК и ИЗМ
        #
        for i in range(128):
            self.fl_task_2.append(
                self.create_flight_task_list_step(type=8, cmd=0x00, pause=1 % 32, repeat=i % 16, data=None))
        self.DCRFlightTaskTimer.singleShot(300, self.send_fl_task_body)
        pass

    def send_fl_task_body(self):
        if 0 <= self.DCRFlightTaskCounter < 1*128:
            self.lm.write_dcr_fl_task_step(ft_num=1, ft_step=self.DCRFlightTaskCounter % 128,
                                           data=self.fl_task_1[self.DCRFlightTaskCounter % 128])
        elif 1*128 <= self.DCRFlightTaskCounter < 2*128:
            self.lm.write_dcr_fl_task_step(ft_num=2, ft_step=self.DCRFlightTaskCounter % 128,
                                           data=self.fl_task_2[self.DCRFlightTaskCounter % 128])
        else:
            self.sendFlTaskPButton.setEnabled(True)
            return
        self.DCRFlightTaskCounter += 1
        self.DCRFlightTaskTimer.singleShot(150, self.send_fl_task_body)

    def cmd_write_fl_task(self):
        self.lm.send_cmd(mode="dcr_ft_1_write")
        time.sleep(0.100)
        self.lm.send_cmd(mode="dcr_ft_2_write")

        pass

    @staticmethod
    def create_flight_task_list_step(type=8, cmd=0x00, pause=1000, repeat=0, data=None):
        step_data_list=[]
        step_data_list.extend([type & 0xFF])
        step_data_list.extend([cmd & 0xFF])
        step_data_list.extend([(pause >> 24) & 0xFF, (pause >> 16) & 0xFF, (pause >> 8) & 0xFF, (pause >> 0) & 0xFF])
        step_data_list.extend([(repeat >> 8) & 0xFF, (repeat >> 0) & 0xFF])
        try:
            data = data[:16]
        except (IndexError, TypeError):
            data = []
        while len(data) < 16:
            data.append(0x00)
        step_data_list.extend(data)
        return step_data_list

    # управление ПН1.1
    def pl11a_set_iku(self):
        self.pl11a.set_out(rst_fpga=self.pl11AResetFPGAChBox.isChecked(),
                           rst_leon=self.pl11AResetMCUChBox.isChecked())
        pass

    def pl11a_write_word(self):
        try:
            u32_addr = self.get_u32_from_ledit(self.pl11AWrAddrLEdit)
            u32_word = self.get_u32_from_ledit(self.pl11AWrDataLEdit)
            self.pl11a.write_data(u32_addr=u32_addr, u32_word=u32_word)
        except Exception as error:
            print("main->write_word->", error)
        pass

    def pl11a_read_word(self):
        try:
            u32_addr = self.get_u32_from_ledit(self.pl11ARdAddrLEdit)
            self.pl11a.read_req_data(u32_addr=u32_addr)
            self.pl11ARdPButton.setEnabled(False)
        except Exception as error:
            print("main->read_word->", error)
        pass

    def pl11a_read_word_slot(self, word):
        self.set_u32_to_ledit(self.pl11ARdDataLEdit, word)
        self.pl11ARdPButton.setEnabled(True)

    def pl11b_set_iku(self):
        self.pl11b.set_out(rst_fpga=self.pl11BResetFPGAChBox.isChecked(),
                           rst_leon=self.pl11BResetMCUChBox.isChecked())
        pass

    def pl11b_write_word(self):
        try:
            u32_addr = self.get_u32_from_ledit(self.pl11BWrAddrLEdit)
            u32_word = self.get_u32_from_ledit(self.pl11BWrDataLEdit)
            self.pl11b.write_data(u32_addr=u32_addr, u32_word=u32_word)
        except Exception as error:
            print("main->write_word->", error)
        pass

    def pl11b_read_word(self):
        try:
            u32_addr = self.get_u32_from_ledit(self.pl11BRdAddrLEdit)
            self.pl11b.read_req_data(u32_addr=u32_addr)
            self.pl11BRdPButton.setEnabled(False)
        except Exception as error:
            print("main->read_word->", error)
        pass

    def pl11b_read_word_slot(self, word):
        self.set_u32_to_ledit(self.pl11BRdDataLEdit, word)
        self.pl11BRdPButton.setEnabled(True)

    def pl12_set_iku(self):
        self.pl12.set_out(n_reset=self.pl12nResetChBox.isChecked(),
                          spi_sel=self.pl12SPISelChBox.isChecked())
        pass

    def pl12_write_word(self):
        try:
            u32_addr = self.get_u32_from_ledit(self.pl12WrAddrLEdit_2)
            u32_word = self.get_u32_from_ledit(self.pl12WrDataLEdit_2)
            self.pl12.write_data(u32_addr=u32_addr, u32_word=u32_word)
        except Exception as error:
            print("main->write_word->", error)
        pass

    def pl12_read_word(self):
        try:
            u32_addr = self.get_u32_from_ledit(self.pl12RdAddrLEdit_2)
            self.pl12.read_req_data(u32_addr=u32_addr)
            self.pl12RdPButton_2.setEnabled(False)
        except Exception as error:
            print("main->read_word->", error)
        pass

    def pl12_read_word_slot(self, word):
        self.set_u32_to_ledit(self.pl12RdDataLEdit_2, word)
        self.pl12RdPButton_2.setEnabled(True)

    def pl20_set_iku(self):
        self.pl20.set_out(ext_reset=self.pl20nResetChBox.isChecked())
        pass

    def pl20_read_word(self):
        try:
            u16_addr = self.get_u16_from_ledit(self.pl20RdAddrLEdit)
            self.pl20.read_req_data_pl20(u16_addr=u16_addr)
            self.pl20RdPButton.setEnabled(False)
        except Exception as error:
            print("main->read_word->", error)
        pass

    def pl20_read_word_slot(self, word):
        self.set_u16_to_ledit(self.pl20RdDataLEdit, word)
        self.pl20RdPButton.setEnabled(True)

    @staticmethod
    def get_u32_from_ledit(line_edit):
        str = line_edit.text()
        str_list = str.split(" ")
        str = "".join(str_list)
        u32val = 0x00000000
        try:
            u32val = int(str, 16)
        except ValueError:
            line_edit.setText("0000 0000")
        return u32val

    @staticmethod
    def get_u16_from_ledit(line_edit):
        str = line_edit.text()
        u16val = 0x0000
        try:
            u16val = int(str, 16)
        except ValueError:
            line_edit.setText("0000")
        return u16val

    @staticmethod
    def set_u32_to_ledit(line_edit, u32val):
        line_edit.setText("%04X %04X" % ((u32val >> 16) & 0xFFFF, (u32val >> 0) & 0xFFFF))
        return u32val

    @staticmethod
    def set_u16_to_ledit(line_edit, u16val):
        line_edit.setText("%04X" % (u16val & 0xFFFF))
        return u16val

    # LOGs #
    @staticmethod
    def create_log_file(file=None, sub_dir="Log", sub_sub_dir=True,  prefix="", extension=".csv"):
        dir_name = "Logs"
        sub_dir_name = dir_name + "\\" + time.strftime("%Y_%m_%d", time.localtime()) + " " + sub_dir
        if sub_sub_dir:
            sub_sub_dir_name = sub_dir_name + "\\" + time.strftime("%Y_%m_%d %H-%M-%S ",
                                                               time.localtime()) + sub_dir
        else:
            sub_sub_dir_name = sub_dir_name
        try:
            os.makedirs(sub_sub_dir_name)
        except (OSError, AttributeError) as error:
            print(error)
            pass
        try:
            if file:
                file.close()
        except (OSError, NameError, AttributeError) as error:
            print(error)
            pass
        file_name = sub_sub_dir_name + "\\" + time.strftime("%Y_%m_%d %H-%M-%S ",
                                                            time.localtime()) + prefix + " " + extension
        file = open(file_name, 'a')
        return file

    def recreate_log_files(self):
        # перезапуск лог файла
        self.data_log_file_title = None
        self.data_log_file = self.create_log_file(file=self.data_log_file, sub_dir="Log", sub_sub_dir=True,
                                                  prefix="Norby_LM",
                                                  extension=".csv")
        pass

    @staticmethod
    def close_log_file(file=None):
        if file:
            try:
                file.close()
            except (OSError, NameError, AttributeError) as error:
                print(error)
            finally:
                file = None
        pass

    #
    def closeEvent(self, event):
        self.close_log_file(file=self.data_log_file)
        self.graph_window.close()
        self.close()
        pass


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    # QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    # os.environ["QT_SCALE_FACTOR"] = "1.0"
    #
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = MainWindow()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение
