#############################################################################
# Copyright (C) 2016 - 2017 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '../spinetoolbox/ui/mainwindow.ui'
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(993, 565)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.mdiArea = QtWidgets.QMdiArea(self.centralwidget)
        self.mdiArea.setViewMode(QtWidgets.QMdiArea.SubWindowView)
        self.mdiArea.setTabsMovable(False)
        self.mdiArea.setObjectName("mdiArea")
        self.subwindow = QtWidgets.QWidget()
        self.subwindow.setObjectName("subwindow")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.subwindow)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.pushButton_datastore_edit = QtWidgets.QPushButton(self.subwindow)
        self.pushButton_datastore_edit.setObjectName("pushButton_datastore_edit")
        self.horizontalLayout_2.addWidget(self.pushButton_datastore_edit)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.subwindow_2 = QtWidgets.QWidget()
        self.subwindow_2.setObjectName("subwindow_2")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.subwindow_2)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_6.addItem(spacerItem2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem3)
        self.pushButton_dc_edit = QtWidgets.QPushButton(self.subwindow_2)
        self.pushButton_dc_edit.setObjectName("pushButton_dc_edit")
        self.horizontalLayout_3.addWidget(self.pushButton_dc_edit)
        self.verticalLayout_6.addLayout(self.horizontalLayout_3)
        self.verticalLayout_7.addLayout(self.verticalLayout_6)
        self.subwindow_3 = QtWidgets.QWidget()
        self.subwindow_3.setObjectName("subwindow_3")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.subwindow_3)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        spacerItem4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem4)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem5)
        self.pushButton_tool_edit = QtWidgets.QPushButton(self.subwindow_3)
        self.pushButton_tool_edit.setObjectName("pushButton_tool_edit")
        self.horizontalLayout.addWidget(self.pushButton_tool_edit)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.verticalLayout_5.addLayout(self.verticalLayout_4)
        self.verticalLayout_3.addWidget(self.mdiArea)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 993, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionQuit = QtWidgets.QAction(MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.actionData_Collection_View = QtWidgets.QAction(MainWindow)
        self.actionData_Collection_View.setObjectName("actionData_Collection_View")
        self.actionDocumentation = QtWidgets.QAction(MainWindow)
        self.actionDocumentation.setObjectName("actionDocumentation")
        self.actionAbout = QtWidgets.QAction(MainWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.actionAdd_Data_Collection = QtWidgets.QAction(MainWindow)
        self.actionAdd_Data_Collection.setObjectName("actionAdd_Data_Collection")
        self.actionAdd_Data_Store = QtWidgets.QAction(MainWindow)
        self.actionAdd_Data_Store.setObjectName("actionAdd_Data_Store")
        self.actionAdd_Tool = QtWidgets.QAction(MainWindow)
        self.actionAdd_Tool.setObjectName("actionAdd_Tool")
        self.menuFile.addAction(self.actionData_Collection_View)
        self.menuFile.addAction(self.actionQuit)
        self.menuHelp.addAction(self.actionAbout)
        self.menuEdit.addAction(self.actionAdd_Data_Collection)
        self.menuEdit.addAction(self.actionAdd_Data_Store)
        self.menuEdit.addAction(self.actionAdd_Tool)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "Spine Toolbox", None, -1))
        self.subwindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "Data Store", None, -1))
        self.pushButton_datastore_edit.setText(QtWidgets.QApplication.translate("MainWindow", "Edit", None, -1))
        self.subwindow_2.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "Data Collection", None, -1))
        self.pushButton_dc_edit.setText(QtWidgets.QApplication.translate("MainWindow", "Edit", None, -1))
        self.subwindow_3.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "Tool", None, -1))
        self.pushButton_tool_edit.setText(QtWidgets.QApplication.translate("MainWindow", "Edit", None, -1))
        self.menuFile.setTitle(QtWidgets.QApplication.translate("MainWindow", "File", None, -1))
        self.menuHelp.setTitle(QtWidgets.QApplication.translate("MainWindow", "Help", None, -1))
        self.menuEdit.setTitle(QtWidgets.QApplication.translate("MainWindow", "Edit", None, -1))
        self.actionQuit.setText(QtWidgets.QApplication.translate("MainWindow", "Quit", None, -1))
        self.actionData_Collection_View.setText(QtWidgets.QApplication.translate("MainWindow", "Open Data Store View", None, -1))
        self.actionDocumentation.setText(QtWidgets.QApplication.translate("MainWindow", "Documentation", None, -1))
        self.actionAbout.setText(QtWidgets.QApplication.translate("MainWindow", "About", None, -1))
        self.actionAdd_Data_Collection.setText(QtWidgets.QApplication.translate("MainWindow", "Add Data Collection", None, -1))
        self.actionAdd_Data_Store.setText(QtWidgets.QApplication.translate("MainWindow", "Add Data Store", None, -1))
        self.actionAdd_Tool.setText(QtWidgets.QApplication.translate("MainWindow", "Add Tool", None, -1))

