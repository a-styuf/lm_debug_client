# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'data_vis_widget.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_dataVisWidgetOName(object):
    def setupUi(self, dataVisWidgetOName):
        dataVisWidgetOName.setObjectName("dataVisWidgetOName")
        dataVisWidgetOName.resize(1074, 653)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(dataVisWidgetOName.sizePolicy().hasHeightForWidth())
        dataVisWidgetOName.setSizePolicy(sizePolicy)
        dataVisWidgetOName.setMinimumSize(QtCore.QSize(750, 100))
        self.verticalLayout = QtWidgets.QVBoxLayout(dataVisWidgetOName)
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtWidgets.QSplitter(dataVisWidgetOName)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.gunitQFrame = QtWidgets.QFrame(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.gunitQFrame.sizePolicy().hasHeightForWidth())
        self.gunitQFrame.setSizePolicy(sizePolicy)
        self.gunitQFrame.setMinimumSize(QtCore.QSize(500, 100))
        self.gunitQFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.gunitQFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.gunitQFrame.setObjectName("gunitQFrame")
        self.dataTableTWidget = QtWidgets.QTableWidget(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dataTableTWidget.sizePolicy().hasHeightForWidth())
        self.dataTableTWidget.setSizePolicy(sizePolicy)
        self.dataTableTWidget.setMinimumSize(QtCore.QSize(200, 100))
        self.dataTableTWidget.setMaximumSize(QtCore.QSize(400, 16777215))
        self.dataTableTWidget.setBaseSize(QtCore.QSize(200, 0))
        self.dataTableTWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.dataTableTWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.dataTableTWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self.dataTableTWidget.setAlternatingRowColors(True)
        self.dataTableTWidget.setRowCount(4)
        self.dataTableTWidget.setObjectName("dataTableTWidget")
        self.dataTableTWidget.setColumnCount(4)
        item = QtWidgets.QTableWidgetItem()
        self.dataTableTWidget.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.dataTableTWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.dataTableTWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignVCenter)
        self.dataTableTWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.dataTableTWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.dataTableTWidget.setItem(0, 0, item)
        self.dataTableTWidget.horizontalHeader().setDefaultSectionSize(30)
        self.dataTableTWidget.horizontalHeader().setMinimumSectionSize(30)
        self.dataTableTWidget.horizontalHeader().setStretchLastSection(True)
        self.dataTableTWidget.verticalHeader().setDefaultSectionSize(30)
        self.dataTableTWidget.verticalHeader().setMinimumSectionSize(30)
        self.verticalLayout.addWidget(self.splitter)
        self.line = QtWidgets.QFrame(dataVisWidgetOName)
        self.line.setMinimumSize(QtCore.QSize(0, 5))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.horizontalLayout.setSpacing(5)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.addUnitPButton = QtWidgets.QPushButton(dataVisWidgetOName)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.addUnitPButton.sizePolicy().hasHeightForWidth())
        self.addUnitPButton.setSizePolicy(sizePolicy)
        self.addUnitPButton.setMinimumSize(QtCore.QSize(30, 30))
        self.addUnitPButton.setMaximumSize(QtCore.QSize(50, 16777215))
        self.addUnitPButton.setObjectName("addUnitPButton")
        self.horizontalLayout.addWidget(self.addUnitPButton)
        self.removeUnitPButton = QtWidgets.QPushButton(dataVisWidgetOName)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.removeUnitPButton.sizePolicy().hasHeightForWidth())
        self.removeUnitPButton.setSizePolicy(sizePolicy)
        self.removeUnitPButton.setMinimumSize(QtCore.QSize(30, 30))
        self.removeUnitPButton.setMaximumSize(QtCore.QSize(50, 16777215))
        self.removeUnitPButton.setObjectName("removeUnitPButton")
        self.horizontalLayout.addWidget(self.removeUnitPButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.setStretch(0, 1)

        self.retranslateUi(dataVisWidgetOName)
        QtCore.QMetaObject.connectSlotsByName(dataVisWidgetOName)

    def retranslateUi(self, dataVisWidgetOName):
        _translate = QtCore.QCoreApplication.translate
        dataVisWidgetOName.setWindowTitle(_translate("dataVisWidgetOName", "data_vis_widget"))
        item = self.dataTableTWidget.verticalHeaderItem(0)
        item.setText(_translate("dataVisWidgetOName", "1"))
        item = self.dataTableTWidget.horizontalHeaderItem(0)
        item.setText(_translate("dataVisWidgetOName", "LY"))
        item = self.dataTableTWidget.horizontalHeaderItem(1)
        item.setText(_translate("dataVisWidgetOName", "RY"))
        item = self.dataTableTWidget.horizontalHeaderItem(2)
        item.setText(_translate("dataVisWidgetOName", "Name"))
        item = self.dataTableTWidget.horizontalHeaderItem(3)
        item.setText(_translate("dataVisWidgetOName", "Val"))
        __sortingEnabled = self.dataTableTWidget.isSortingEnabled()
        self.dataTableTWidget.setSortingEnabled(False)
        self.dataTableTWidget.setSortingEnabled(__sortingEnabled)
        self.addUnitPButton.setText(_translate("dataVisWidgetOName", "Add"))
        self.removeUnitPButton.setText(_translate("dataVisWidgetOName", "Rmv"))
