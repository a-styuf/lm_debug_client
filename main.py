import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
import main_win
import lm_data
import time
import os


class MainWindow(QtWidgets.QMainWindow, main_win.Ui_MainWindow):
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле main_win.py
        #
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.setWindowTitle("Norby - Linking Module")
        # класс для управления устройством
        self.lm = lm_data.LMData(serial_numbers=["205135995748"], debug=True, address=6)
        self.connectionPButt.clicked.connect(self.lm.serial.reconnect)
        # управление питанием МС
        self.pwrChsSetPButton.clicked.connect(self.pwr_set_channels_state)
        self.pwrDataGetPButton.clicked.connect(self.pwr_get_channels_data)
        self.cycleReadPWRDataPButton.clicked.connect(self.pwr_cycle_read_data)
        self.PWRReadTimer = QtCore.QTimer()
        self.PWRReadTimer.timeout.connect(self.pwr_get_channels_data)

        self.allChannelsChBox.clicked.connect(self.pwr_all_channel_choice)
        self.pwr_channels_list = [self.lmChannelsChBox, self.pl11aChannelsChBox, self.pl11bChannelsChBox,
                                  self.pl12ChannelsChBox, self.pl20ChannelsChBox, self.dcr1ChannelsChBox,
                                  self.dcr2ChannelsChBox]
        # заполнение таблицы с параметрами
        self.channels_data_tables_init()
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
    def channels_data_tables_init(self):
        row_height = 10
        column_width = 90
        self.pwrDataTWidget.setRowCount(len(self.lm.pwr_chan_names))
        self.pwrDataTWidget.setColumnCount(2)
        self.pwrDataTWidget.setVerticalHeaderLabels(self.lm.pwr_chan_names)
        self.pwrDataTWidget.setHorizontalHeaderLabels(["V", "mA"])
        for column in range(self.pwrDataTWidget.columnCount()):
            self.pwrDataTWidget.setColumnWidth(column, column_width)
        for row in range(self.pwrDataTWidget.rowCount()):
            self.pwrDataTWidget.setRowHeight(row, row_height)
        self.pwrDataTWidget.setMinimumWidth(self.pwrDataTWidget.columnCount()*column_width+110)
        self.pwrDataTWidget.setMinimumHeight(self.pwrDataTWidget.rowCount()*row_height+20)

    def update_ui(self):
        try:
            # заполнение таблицы данных с питанием
            for row in range(len(self.lm.pwr_chan_names)):
                #
                table_item_V = QtWidgets.QTableWidgetItem("%.2f" % self.lm.voltage_data[row])
                table_item_V.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                #
                table_item_mA = QtWidgets.QTableWidgetItem("%.2f" % self.lm.current_data[row])
                table_item_mA.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                #
                self.pwrDataTWidget.setItem(row, 0, table_item_V)
                self.pwrDataTWidget.setItem(row, 1, table_item_mA)
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
            self.statusLEdit.setText(self.lm.serial.state_string[self.lm.serial.state])
        except Exception as error:
            print("update_ui: " + str(error))

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
        self.lm.send_cmd(mode="pwr_on_off", data=[channel_state])
        pass

    def pwr_get_channels_data(self):
        self.lm.send_cmd(mode="pwr_tmi", data=[])
        pass

    def pwr_cycle_read_data(self):
        if self.PWRReadTimer.isActive():
            self.PWRReadTimer.stop()
        else:
            self.PWRReadTimer.start(1000)
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
