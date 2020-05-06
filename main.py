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


version = "0.5.0"


class MainWindow(QtWidgets.QMainWindow, main_win.Ui_MainWindow):
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле main_win.py
        #
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.setWindowTitle("Norby - Linking Module. Version {:s}.".format(version))
        # класс для управления устройством
        self.lm = lm_data.LMData(serial_numbers=["205135995748", "205B359A", "2056359A", "2059359A"], debug=True, address=6)
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
        # работа с циклограммами
        self.singleCyclPButton.clicked.connect(self.single_cyclogram)
        self.startCyclsPButton.clicked.connect(self.start_cyclograms)
        self.stopCyclsPButton.clicked.connect(self.stop_cyclograms)
        # работа с ДеКоР
        self.DCRModeDefaultPButton.clicked.connect(self.set_dcr_mode_default)
        self.DCRModeFlightTaskPButton.clicked.connect(self.set_dcr_mode_flight_task)
        self.DCRModePausePButton.clicked.connect(self.set_dcr_mode_pause)
        self.DCRModeOffPButton.clicked.connect(self.set_dcr_mode_off)
        # работа с ПН1.1
        self.pl11a = pay_load.PayLoad_11(lm=self.lm)

        self.pl11ASetIKUPButton.clicked.connect(self.set_pl11a_iku)
        # обновление gui
        self.DataUpdateTimer = QtCore.QTimer()
        self.DataUpdateTimer.timeout.connect(self.update_ui)
        self.DataUpdateTimer.start(1000)
        # логи
        self.data_log_file = None
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
        self.lm.send_cmd_reg(mode="dbg_cyclogram_start", data=[0x01, cyclogram_num])
        pass

    def start_cyclograms(self):
        self.lm.send_cmd_reg(mode="dbg_cyclogram_start", data=[0x02, 0x00])
        pass

    def stop_cyclograms(self):
        self.lm.send_cmd_reg(mode="dbg_cyclogram_start", data=[0x00, 0x00])
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

    # управление ПН1.1А
    def set_pl11a_iku(self):
        self.pl11a.set_out(rst_fpga=self.pl11AResetFPGAChBox.isChecked(),
                           rst_leon=self.pl11AResetMCUChBox.isChecked())
        pass

    # LOGs #
    @staticmethod
    def create_log_file(file=None, prefix="", extension=".csv"):
        dir_name = "Logs"
        sub_dir_name = dir_name + "\\" + time.strftime("%Y_%m_%d", time.localtime()) + " Log"
        sub_sub_dir_name = sub_dir_name + "\\" + time.strftime("%Y_%m_%d %H-%M-%S ",
                                                               time.localtime()) + "Log"
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
