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

version = "0.9.1"


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
        self.lm = lm_data.LMData(serial_numbers=["0000ACF0", "205135995748", "205B359A", "2056359A", "2059359A"], debug=True, address=6)
        self.connectionPButt.clicked.connect(self.lm.usb_can.reconnect)
        # таб с кан-терминалом
        self.can_usb_client_widget = can_unit.ClientGUIWindow(self, interface=self.lm.usb_can)
        self.canTerminalVBLayout = QtWidgets.QVBoxLayout()
        self.canTerminalTab.setLayout(self.canTerminalVBLayout)
        self.canTerminalVBLayout.addWidget(self.can_usb_client_widget)
        # второе окно с графиками
        self.graph_window = data_vis.Widget()
        self.openGraphPButton.clicked.connect(self.open_graph_window)
        # управление питанием МС
        self.pwrChsSetPButton.clicked.connect(self.pwr_set_channels_state)
        #
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
        self.DCRModeDefaultPButton.clicked.connect(self.set_dcr_mode_default)
        self.DCRModeFlightTaskPButton.clicked.connect(self.set_dcr_mode_flight_task)
        self.DCRModePausePButton.clicked.connect(self.set_dcr_mode_pause)
        self.DCRModeOffPButton.clicked.connect(self.set_dcr_mode_off)
        # работа с ПН1.1А
        self.pl11a = pay_load.PayLoad_11(self, lm=self.lm, pl_type="pl11_a")
        self.pl11a.instamessage_signal.connect(self.pl11a_read_word_slot)
        self.pl11AWrPButton.clicked.connect(self.pl11a_write_word)
        self.pl11ARdPButton.clicked.connect(self.pl11a_read_word)

        self.pl11TestTimer = QtCore.QTimer()

        self.pl11ASetIKUPButton.clicked.connect(self.pl11a_set_iku)
        # работа с ПН1.1Б
        self.pl11b = pay_load.PayLoad_11(self, lm=self.lm, pl_type="pl11_b")
        self.pl11b.instamessage_signal.connect(self.pl11b_read_word_slot)
        self.pl11BWrPButton.clicked.connect(self.pl11b_write_word)
        self.pl11BRdPButton.clicked.connect(self.pl11b_read_word)

        self.pl11BSetIKUPButton.clicked.connect(self.pl11b_set_iku)
        # обновление gui
        self.DataUpdateTimer = QtCore.QTimer()
        self.DataUpdateTimer.timeout.connect(self.update_ui)
        self.DataUpdateTimer.start(1000)
        # логи
        self.data_log_file = None
        self.cycl_res_log_file = None
        self.log_str = ""
        self.recreate_log_files()
        self.logRestartPButt.clicked.connect(self.recreate_log_files)

        # UI #
    def update_ui(self):
        try:
            # отрисовка графика
            pass
            # логи
            log_str_tmp = self.lm.get_log_file_data()
            if self.log_str == log_str_tmp:
                pass
            else:
                self.log_str = log_str_tmp
                self.data_log_file.write(self.log_str + "\n")
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
        self.lm.read_tmi(mode="lm_full_tmi")
        pass

    def cycle_get_general_data(self):
        if self.genDataReadTimer.isActive():
            self.genDataReadTimer.stop()
        else:
            self.genDataReadTimer.start(1000)
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
        if self.readCyclResCounter < 17:
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


    # управление ДеКоР
    def set_dcr_mode_default(self):
        self.lm.send_cmd_reg(mode="pn_dcr_mode", data=[0x01])
        pass

    def set_dcr_mode_flight_task(self):
        self.lm.send_cmd_reg(mode="pn_dcr_mode", data=[0x02])
        pass

    def set_dcr_mode_pause(self):
        self.lm.send_cmd_reg(mode="pn_dcr_mode", data=[0x03])
        pass

    def set_dcr_mode_off(self):
        self.lm.send_cmd_reg(mode="pn_dcr_mode", data=[0x00])
        pass

    # управление ПН1.1
    def pl11a_set_iku(self):
        self.pl11a.set_out(rst_fpga=self.pl11AResetFPGAChBox.isChecked(),
                           rst_leon=self.pl11AResetMCUChBox.isChecked())
        pass

    def pl11b_set_iku(self):
        self.pl11b.set_out(rst_fpga=self.pl11BResetFPGAChBox.isChecked(),
                           rst_leon=self.pl11BResetMCUChBox.isChecked())
        pass

    def pl11a_write_word(self):
        try:
            u32_addr = self.get_u32_from_ledit(self.pl11AWrAddrLEdit)
            u32_word = self.get_u32_from_ledit(self.pl11AWrDataLEdit)
            self.pl11a.write_data(u32_addr=u32_addr, u32_word=u32_word)
        except Exception as error:
            print("main->write_word->", error)
        pass

    def pl11b_write_word(self):
        try:
            u32_addr = self.get_u32_from_ledit(self.pl11BWrAddrLEdit)
            u32_word = self.get_u32_from_ledit(self.pl11BWrDataLEdit)
            self.pl11b.write_data(u32_addr=u32_addr, u32_word=u32_word)
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

    def pl11b_read_word(self):
        try:
            u32_addr = self.get_u32_from_ledit(self.pl11BRdAddrLEdit)
            self.pl11b.read_req_data(u32_addr=u32_addr)
            self.pl11BRdPButton.setEnabled(False)
        except Exception as error:
            print("main->read_word->", error)
        pass

    def pl11a_read_word_slot(self, word):
        self.set_u32_to_ledit(self.pl11ARdDataLEdit, word)
        self.pl11ARdPButton.setEnabled(True)

    def pl11b_read_word_slot(self, word):
        self.set_u32_to_ledit(self.pl11BRdDataLEdit, word)
        self.pl11BRdPButton.setEnabled(True)

    def get_u32_from_ledit(self, line_edit):
        str = line_edit.text()
        str_list = str.split(" ")
        str = "".join(str_list)
        u32val = 0x00000000
        try:
            u32val = int(str, 16)
        except ValueError:
            line_edit.setText("0000 0000")
        return u32val

    def set_u32_to_ledit(self, line_edit, u32val):
        line_edit.setText("%04X %04X" % ((u32val >> 16) & 0xFFFF, (u32val >> 0) & 0xFFFF))
        return u32val

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
        self.data_log_file = self.create_log_file(prefix="Norby_LM", extension=".csv")
        # заголовки
        self.data_log_file.write("Title" + "\n")
        pass

    @staticmethod
    def close_log_file(file=None):
        if file:
            try:
                file.close()
            except (OSError, NameError, AttributeError) as error:
                print(error)
                pass
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
