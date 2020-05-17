from PyQt5 import QtWidgets, QtCore
import cyclogram_result_win


class Widget(QtWidgets.QWidget, cyclogram_result_win.Ui_CyclogramResult):
    def __init__(self):
        # unit-GUI initialization
        super(Widget, self).__init__()
        self.setupUi(self)
