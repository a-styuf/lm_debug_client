# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'cyclogram_result_win.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_CyclogramResult(object):
    def setupUi(self, CyclogramResult):
        CyclogramResult.setObjectName("CyclogramResult")
        CyclogramResult.resize(1024, 761)
        self.horizontalLayout = QtWidgets.QHBoxLayout(CyclogramResult)
        self.horizontalLayout.setContentsMargins(5, 5, 5, 5)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cyclResultTEdit = QtWidgets.QTextEdit(CyclogramResult)
        self.cyclResultTEdit.setReadOnly(True)
        self.cyclResultTEdit.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.cyclResultTEdit.setObjectName("cyclResultTEdit")
        self.horizontalLayout.addWidget(self.cyclResultTEdit)

        self.retranslateUi(CyclogramResult)
        QtCore.QMetaObject.connectSlotsByName(CyclogramResult)

    def retranslateUi(self, CyclogramResult):
        _translate = QtCore.QCoreApplication.translate
        CyclogramResult.setWindowTitle(_translate("CyclogramResult", "Cyclogram Result"))
