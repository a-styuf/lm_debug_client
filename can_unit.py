import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QColor
import usb_can_bridge
import can_unit_widget
import can_usb_bridge_client_widget
import norby_data
import configparser
import os
import can_usb_bridge_client_win
import time


class Widget(QtWidgets.QFrame, can_unit_widget.Ui_Frame):

    action_signal = QtCore.pyqtSignal([list])

    def __init__(self, parent, **kw):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле design.py
        super().__init__(parent)
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        # инициаллизация МКО #
        self.num = 0
        self.name = "..."
        for key in sorted(kw):
            if key == "interface":
                self.interface = kw.pop(key)
            elif key == "num":
                self.num = kw.pop(key)
            elif key == "name":
                self.name = kw.pop(key)
            else:
                pass
        # конфигурация
        self.cfg_dict = {"name": "Name",
                         "channel_num": "0",
                         "dev_id": "6",
                         "var_id": "5",
                         "offset": "0",
                         "length": "128",
                         "data": " ".join(["0" for i in range(128)]),
                         "mode": "read",
                         }
        self.state = 0
        self.action_state = 0
        self.bus_state = 0
        self.channel_num = 0
        self.dev_id = 0
        self.var_id = 0
        self.offset = 0
        self.length = 0
        self.data = [0, 0]
        self.table_data = [["Нет данных", ""]]
        #
        self.total_cnt = 1
        self.aw_err_cnt = 0
        self.time_out = 0
        #
        self.load_cfg()
        #
        self.numLabel.setText("%d" % self.num)
        self.actionPButton.clicked.connect(self.action)
        #
        self.request_timer = QtCore.QTimer()
        self.request_timer.timeout.connect(self.set_data_to_unit)

    def set_num(self, n):
        self.num = n
        self.numLabel.setText("%d" % self.num)

    def load_cfg(self, cfg_dict=None):
        if cfg_dict:
            self.cfg_dict = cfg_dict
        #
        self.name = self.cfg_dict.get("name", "NA")
        self.nameLine.setText(self.name)
        #
        self.channel_num = self.cfg_dict.get("channel_num", "0")
        self.CANChanNUMSBox.setValue(int(self.channel_num))
        #
        self.dev_id = self.cfg_dict.get("dev_id", "1")
        self.devIDSBox.setValue(int(self.dev_id))
        #
        self.var_id = self.cfg_dict.get("var_id", "0")
        self.varIDSBox.setValue(int(self.var_id))
        #
        self.offset = self.cfg_dict.get("offset", "0")
        self.offsetSBox.setValue(int(self.offset))
        #
        self.length = self.cfg_dict.get("length", "0")
        self.lengthSBox.setValue(int(self.length))
        #
        data = self.cfg_dict.get("data", "0000").split(" ")
        self.data = [int(var, 16) for var in data]
        self.insert_data(self.data)
        #
        self.action_state = 0 if self.cfg_dict.get("mode", "read") in "read" else 1
        if self.action_state == 0:
            self.modeBox.setCurrentText("Чтение")
        else:
            self.modeBox.setCurrentText("Запись")

    def get_cfg(self):
        self.name = self.nameLine.text()
        self.cfg_dict["name"] = self.name
        #
        self.channel_num = self.CANChanNUMSBox.value()
        self.cfg_dict["dev_id"] = "%d" % self.channel_num
        #
        self.dev_id = self.devIDSBox.value()
        self.cfg_dict["dev_id"] = "%d" % self.dev_id
        #
        self.var_id = self.varIDSBox.value()
        self.cfg_dict["var_id"] = "%d" % self.var_id
        #
        self.offset = self.offsetSBox.value()
        self.cfg_dict["offset"] = "%d" % self.offset
        #
        self.length = self.lengthSBox.value()
        self.cfg_dict["length"] = "%d" % self.length
        #
        self.cfg_dict["mode"] = "read" if self.modeBox.currentText() in "Чтение" else "write"
        #
        self.get_data()
        if self.modeBox.currentText() == "Чтение":
            pass
        else:
            self.cfg_dict["data"] = " ".join(["%04X" % var for var in self.data])
        return self.cfg_dict

    def write(self):
        if self.interface.is_open:
            self.interface.request(can_num=int(self.CANChanNUMSBox.value()),
                                   dev_id=int(self.devIDSBox.value()),
                                   mode="write",
                                   var_id=int(self.varIDSBox.value()),
                                   offset=int(self.offsetSBox.value()),
                                   d_len=int(self.lengthSBox.value()),
                                   data=self.get_data_bytes(int(self.lengthSBox.value()))
                                   )
            self.state = 0
        else:
            self.state = 2
        self.state_check()
        pass

    def read(self):
        if self.interface.is_open:
            self.actionPButton.setEnabled(False)
            self.interface.request(can_num=int(self.CANChanNUMSBox.value()),
                                   dev_id=int(self.devIDSBox.value()),
                                   mode="read",
                                   var_id=int(self.varIDSBox.value()),
                                   offset=int(self.offsetSBox.value()),
                                   d_len=int(self.lengthSBox.value()),
                                   data=[]
                                   )
            self.request_timer.singleShot(200, self.set_data_to_unit)
            self.time_out = 7
            self.state = 0
        else:
            self.state = 2
        self.state_check()
        pass

    def set_data_to_unit(self):
        self.total_cnt += 1
        id_var, data = self.interface.get_data()
        self.idVarLine.setText("0x{:04X}".format(id_var))
        if id_var != 0x0000:
            if self.modeBox.currentText() in "Чтение":  # read
                self.insert_data(data)
            self.state = 0
            self.get_data()
            self.table_data = norby_data.frame_parcer(self.data)
            # при приеме инициируем сигнал, который запустит отображение таблицы данных
            self.action_signal.emit(self.table_data)
        else:
            self.state = 1
        self.actionPButton.setEnabled(True)
        self.state_check()
        pass

    def action(self):
        if self.modeBox.currentText() in "Чтение":  # read
            self.read()
            self.table_data = norby_data.frame_parcer(self.data)
        else:
            self.write()
        pass

    def state_check(self):
        if self.state == 1:
            self.statusLabel.setText("CAN-USB")
            self.statusLabel.setStyleSheet('QLabel {background-color: orangered;}')
        elif self.state == 2:
            self.statusLabel.setText("Подключение")
            self.statusLabel.setStyleSheet('QLabel {background-color: coral;}')
        elif self.state == 0:
            self.statusLabel.setText("Норма")
            self.statusLabel.setStyleSheet('QLabel {background-color: seagreen;}')
        pass

    def connect(self):
        # todo обдумать возможность использования данной функции
        return self.state

    def insert_data(self, data):
        for row in range(self.dataTable.rowCount()):
            for column in range(self.dataTable.columnCount()):
                try:
                    table_item = QtWidgets.QTableWidgetItem("%04X" % data[row*8 + column])
                except (IndexError, TypeError):
                    table_item = QtWidgets.QTableWidgetItem(" ")
                self.dataTable.setItem(row, column, table_item)
        pass

    def get_data(self):
        data = []
        for row in range(self.dataTable.rowCount()):
            for column in range(self.dataTable.columnCount()):
                try:
                    data.append(int(self.dataTable.item(row, column).text(), 16))
                except ValueError:
                    data.append(0)
        self.data = data
        return self.data

    def get_data_bytes(self, length):
        data = []
        data_words = self.get_data()
        for var in data_words:
            data.append((var >> 8) & 0xFF)
            data.append((var >> 0) & 0xFF)
        return data[:length]


class Widgets(QtWidgets.QVBoxLayout):
    action = QtCore.pyqtSignal([list])

    def __init__(self, parent, **kw):
        super().__init__(parent)
        for key in sorted(kw):
            if key == "interface":
                self.interface = kw.pop(key)
        self.parent = parent
        self.unit_list = []
        #
        self.total_cnt = 1
        self.aw_err_cnt = 0
        pass

    def add_unit(self):
        widget_to_add = Widget(self.parent, num=len(self.unit_list), interface=self.interface)
        self.unit_list.append(widget_to_add)
        self.addWidget(widget_to_add)
        widget_to_add.action_signal.connect(self.multi_action)
        pass

    def multi_action(self, table_data):
        sender = self.sender()
        #
        self.aw_err_cnt += sender.aw_err_cnt
        self.total_cnt += sender.total_cnt
        #
        self.action.emit(table_data)

    def delete_unit_by_num(self, n):
        try:
            widget_to_dlt = self.unit_list.pop(n)
            widget_to_dlt.deleteLater()
            # self.unit_layout.removeWidget(widget_to_dlt)
            for i in range(len(self.unit_list)):
                self.unit_list[i].set_num(i)
        except IndexError:
            pass
        self.update()
        pass

    def delete_all_units(self):
        for i in range(self.count()):
            self.itemAt(0).widget().close()
            self.takeAt(0)
        self.unit_list = []
        pass

    def redraw(self):
        self.update()
        pass

    def get_cfg(self, config):
        for i in range(len(self.unit_list)):
            cfg_dict = self.unit_list[i].get_cfg()
            config["Unit %d" % i] = cfg_dict
        return config

    def load_cfg(self, config):
        units_cfg = config.sections()
        self.delete_all_units()
        for i in range(len(units_cfg)):
            if "Unit" in units_cfg[i]:
                self.add_unit()
                self.unit_list[-1].load_cfg(config[units_cfg[i]])
        return config


class ClientGUIWindow(QtWidgets.QFrame, can_usb_bridge_client_widget.Ui_Form):
    def __init__(self, parent, **kw):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле design.py
        super().__init__(parent)
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        #
        self.interface = None
        self.serial_number = "000000000000"
        for key in sorted(kw):
            if key == "interface":
                self.interface = kw.pop(key)
        #
        self.config = None
        #
        if self.interface is None:
            self.interface = usb_can_bridge.MyUSBCANDevice(serial_numbers=[], debug=True)
        # контейнеры для вставки юнитов
        self.units_widgets = Widgets(self.unitsSArea, interface=self.interface)
        self.units_widgets.action.connect(self.data_table_slot)
        self.setLayout(self.units_widgets)
        # привязка сигналов к кнопкам
        #
        self.addUnitPButton.clicked.connect(self.units_widgets.add_unit)
        self.dltUnitPButt.clicked.connect(self.dlt_unit)
        self.dltAllUnitsPButt.clicked.connect(self.units_widgets.delete_all_units)
        #
        self.loadCfgPButt.clicked.connect(self.load_cfg)
        self.saveCfgPButt.clicked.connect(self.save_cfg)
        # таймер для работы с циклами опросов
        self.cycleTimer = QtCore.QTimer()
        self.cycleTimer.timeout.connect(self.start_request_cycle)
        self.cycle_step_count = 0
        self.cycleStartPButton.clicked.connect(lambda: self.cycleTimer.start(1000))
        self.cycleStopPButton.clicked.connect(self.stop_request_cycle)
        #
        self.connectionPButton.clicked.connect(self.connect)
        #
        self.load_init_cfg()
        self.interface.serial_numbers.append(self.serial_number)
        # LOG-s files
        self.can_log_file = None
        self.serial_log_file = None
        self.recreate_log_files()
        # timers for different purpose
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.update_data)
        self.updateTimer.start(1000)

    def update_data(self):
        # log_files
        for log_str in self.interface.get_can_log():
            self.can_log_file.write(log_str + "\n")
        for log_str in self.interface.get_serial_log():
            self.serial_log_file.write(log_str + "\n")
        # state check
        self.connectionPButton.setText(self.interface.state_check()[0])
        self.connectionPButton.setStyleSheet('QPushButton {background-color: %s;}' % (self.interface.state_check()[1]))
        pass

    def connect(self):
        self.serial_number = self.devIDLEdit.text()
        self.interface.serial_numbers.append(self.serial_number)
        self.interface.reconnect()

        pass

    def start_request_cycle(self):
        period = self.cycleIntervalSBox_3.value()
        self.cycleTimer.setInterval(period * 1000)
        #
        unit_num = len(self.units_widgets.unit_list)
        if self.cycle_step_count == 0:
            self.cycle_step_count = self.cycleNumSBox_3.value() * unit_num
            return
        else:
            self.cycle_step_count -= 1
            # print("%04X" % self.kpa.mko_aw)
            if self.cycle_step_count == 0:
                self.stop_request_cycle()
        elapsed_time = period * self.cycle_step_count
        self.cycleElapsedTimeEdit.setTime(QtCore.QTime(0, 0).addSecs(elapsed_time))
        #
        self.units_widgets.unit_list[(unit_num - 1) - (self.cycle_step_count % unit_num)].action()
        #
        try:
            self.cyclePrBar.setValue(100 - ((100 * self.cycle_step_count) / (self.cycleNumSBox_3.value() * unit_num)))
        except ValueError:
            self.cyclePrBar.setValue(100)
        pass

    def stop_request_cycle(self):
        self.cyclePrBar.setValue(0)
        self.cycleTimer.stop()
        self.cycle_step_count = 0
        self.cycleElapsedTimeEdit.setTime(QtCore.QTime(0, 0))
        pass

    def data_table_slot(self, table_data):
        # на всякий пожарный сохраняем текущую конфигурацию
        self.save_init_cfg()
        #
        self.dataTWidget.setRowCount(len(table_data))
        for row in range(len(table_data)):
            for column in range(self.dataTWidget.columnCount()):
                try:
                    table_item = QtWidgets.QTableWidgetItem(table_data[row][column])
                    self.dataTWidget.setItem(row, column, table_item)
                except IndexError:
                    pass
        pass

    def dlt_unit(self):
        n = self.dltUnitNumSBox.value()
        self.units_widgets.delete_unit_by_num(n)
        pass

    def load_init_cfg(self):
        self.config = configparser.ConfigParser()
        file_name = "CAN-USB_init.cfg"
        self.config.read(file_name)
        if self.config.sections():
            self.units_widgets.load_cfg(self.config)
        else:
            self.units_widgets.add_unit()
        try:
            self.serial_number = self.config["usb_can bridge device"]["id"]
            self.devIDLEdit.setText(self.config["usb_can bridge device"]["id"])
        except KeyError as error:
            print(error)
        pass

    def save_init_cfg(self):
        self.config = configparser.ConfigParser()
        self.config = self.units_widgets.get_cfg(self.config)
        self.config["usb_can bridge device"] = {"id": self.devIDLEdit.text()}
        file_name = "CAN-USB_init.cfg"
        try:
            with open(file_name, 'w') as configfile:
                self.config.write(configfile)
        except FileNotFoundError:
            pass
        pass

    def load_cfg(self):
        config = configparser.ConfigParser()
        home_dir = os.getcwd()
        try:
            os.mkdir(home_dir + "\\CAN-USB_Config")
        except OSError as error:
            pass
        file_name = QtWidgets.QFileDialog.getOpenFileName(self,
                                                          "Открыть файл конфигурации",
                                                          home_dir + "\\CAN-USB_Config",
                                                          r"config(*.cfg);;All Files(*)")[0]
        config.read(file_name)
        try:
            self.interface.serial_numbers.append(config["usb_can bridge device"]["id"])
            self.devIDLEdit.setText(config["usb_can bridge device"]["id"])
        except KeyError as error:
            pass
        self.units_widgets.load_cfg(config)
        pass

    def save_cfg(self):
        home_dir = os.getcwd()
        config = configparser.ConfigParser()
        config = self.units_widgets.get_cfg(config)
        config["usb_can bridge device"] = {"id": self.devIDLEdit.text()}
        try:
            os.mkdir(home_dir + "\\CAN-USB_Config")
        except OSError:
            pass
        file_name = QtWidgets.QFileDialog.getSaveFileName(self,
                                                          "Сохранить файл конфигурации",
                                                          home_dir + "\\CAN-USB_Config",
                                                          r"config(*.cfg);;All Files(*)")[0]
        try:
            configfile = open(file_name, 'w')
            config.write(configfile)
            configfile.close()
        except FileNotFoundError as error:
            pass
        pass

    # LOGs #
    @staticmethod
    def create_log_file(file=None, prefix="", dir_prefix="", extension=".txt"):
        dir_name = "Logs"
        sub_dir_name = dir_name + "\\" + time.strftime("%Y_%m_%d ", time.localtime()) + dir_prefix
        sub_sub_dir_name = sub_dir_name + "\\" + time.strftime("%Y_%m_%d %H-%M-%S ",
                                                               time.localtime()) + dir_prefix
        try:
            os.makedirs(sub_sub_dir_name)
        except (OSError, AttributeError) as error:
            pass
        try:
            if file:
                file.close()
        except (OSError, NameError, AttributeError) as error:
            pass
        file_name = sub_sub_dir_name + "\\" + time.strftime("%Y_%m_%d %H-%M-%S ",
                                                            time.localtime()) + dir_prefix + " " + prefix + extension
        file = open(file_name, 'a')
        return file

    @staticmethod
    def close_log_file(file=None):
        if file:
            try:
                file.close()
            except (OSError, NameError, AttributeError) as error:
                pass
        pass

    def recreate_log_files(self):
        self.can_log_file = self.create_log_file(prefix="can", dir_prefix="CAN-USB_bridge")
        self.serial_log_file = self.create_log_file(prefix="serial", dir_prefix="CAN-USB_bridge")
        pass

    def closeEvent(self, event):
        self.close_log_file(self.serial_log_file)
        self.close_log_file(self.can_log_file)


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем

    class MainWindow(QtWidgets.QMainWindow, can_usb_bridge_client_win.Ui_MainWindow):
        def __init__(self):
            # Это здесь нужно для доступа к переменным, методам
            # и т.д. в файле design.py
            #
            super().__init__()
            self.setupUi(self)  # Это нужно для инициализации нашего дизайна
            #
            self.can_usb_client_widget = ClientGUIWindow(self)
            self.gridLayout.addWidget(self.can_usb_client_widget, 0, 0, 1, 1)

        def closeEvent(self, event):
            self.can_usb_client_widget.save_init_cfg()
            pass

    # QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    # os.environ["QT_SCALE_FACTOR"] = "1.0"
    #
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = MainWindow()  # Создаём объект класса ExampleApp
    window.show()
    app.exec_()  # и запускаем приложение