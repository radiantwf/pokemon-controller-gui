# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_form.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGroupBox, QLabel, QMainWindow, QPushButton,
    QSizePolicy, QStatusBar, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(960, 700)
        MainWindow.setMinimumSize(QSize(960, 700))
        MainWindow.setMaximumSize(QSize(960, 700))
        self.actionCOM1 = QAction(MainWindow)
        self.actionCOM1.setObjectName(u"actionCOM1")
        self.action_5 = QAction(MainWindow)
        self.action_5.setObjectName(u"action_5")
        self.actionCamera1 = QAction(MainWindow)
        self.actionCamera1.setObjectName(u"actionCamera1")
        self.actionCamera2 = QAction(MainWindow)
        self.actionCamera2.setObjectName(u"actionCamera2")
        self.actionStart = QAction(MainWindow)
        self.actionStart.setObjectName(u"actionStart")
        self.actionStop = QAction(MainWindow)
        self.actionStop.setObjectName(u"actionStop")
        self.actionRescan = QAction(MainWindow)
        self.actionRescan.setObjectName(u"actionRescan")
        self.actionAudio1 = QAction(MainWindow)
        self.actionAudio1.setObjectName(u"actionAudio1")
        self.actionAudio2 = QAction(MainWindow)
        self.actionAudio2.setObjectName(u"actionAudio2")
        self.actionRescan_2 = QAction(MainWindow)
        self.actionRescan_2.setObjectName(u"actionRescan_2")
        self.actionMute = QAction(MainWindow)
        self.actionMute.setObjectName(u"actionMute")
        self.actionSettings = QAction(MainWindow)
        self.actionSettings.setObjectName(u"actionSettings")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.lblCameraPlayer = QLabel(self.centralwidget)
        self.lblCameraPlayer.setObjectName(u"lblCameraPlayer")
        self.lblCameraPlayer.setGeometry(QRect(10, 10, 640, 360))
        self.lblCameraPlayer.setFrameShape(QFrame.StyledPanel)
        self.lblCameraPlayer.setFrameShadow(QFrame.Plain)
        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 380, 641, 81))
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(10, 25, 30, 26))
        self.label_3.setMinimumSize(QSize(30, 0))
        self.label_3.setMaximumSize(QSize(30, 16777215))
        self.cbxCameraList = QComboBox(self.groupBox)
        self.cbxCameraList.setObjectName(u"cbxCameraList")
        self.cbxCameraList.setGeometry(QRect(50, 25, 240, 26))
        self.cbxCameraList.setMinimumSize(QSize(240, 0))
        self.cbxCameraList.setMaximumSize(QSize(240, 16777215))
        self.btnCameraOpt = QPushButton(self.groupBox)
        self.btnCameraOpt.setObjectName(u"btnCameraOpt")
        self.btnCameraOpt.setGeometry(QRect(290, 23, 60, 26))
        self.btnCameraOpt.setMinimumSize(QSize(60, 0))
        self.btnCameraOpt.setMaximumSize(QSize(60, 16777215))
        self.btnRescan = QPushButton(self.groupBox)
        self.btnRescan.setObjectName(u"btnRescan")
        self.btnRescan.setGeometry(QRect(550, 25, 80, 51))
        self.btnRescan.setMinimumSize(QSize(80, 0))
        self.btnRescan.setMaximumSize(QSize(60, 16777215))
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(370, 25, 30, 26))
        self.label_2.setMinimumSize(QSize(30, 0))
        self.label_2.setMaximumSize(QSize(30, 16777215))
        self.cbxFps = QComboBox(self.groupBox)
        self.cbxFps.addItem("")
        self.cbxFps.addItem("")
        self.cbxFps.addItem("")
        self.cbxFps.addItem("")
        self.cbxFps.addItem("")
        self.cbxFps.addItem("")
        self.cbxFps.setObjectName(u"cbxFps")
        self.cbxFps.setGeometry(QRect(410, 25, 60, 26))
        self.cbxFps.setMaximumSize(QSize(60, 40))
        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(10, 50, 30, 26))
        self.label_6.setMinimumSize(QSize(30, 0))
        self.label_6.setMaximumSize(QSize(30, 16777215))
        self.cbxAudioList = QComboBox(self.groupBox)
        self.cbxAudioList.setObjectName(u"cbxAudioList")
        self.cbxAudioList.setGeometry(QRect(50, 50, 240, 26))
        self.cbxAudioList.setMinimumSize(QSize(240, 0))
        self.cbxAudioList.setMaximumSize(QSize(240, 16777215))
        self.chbMute = QCheckBox(self.groupBox)
        self.chbMute.setObjectName(u"chbMute")
        self.chbMute.setGeometry(QRect(290, 50, 87, 26))
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionCOM1.setText(QCoreApplication.translate("MainWindow", u"COM1", None))
        self.action_5.setText(QCoreApplication.translate("MainWindow", u"\u6dfb\u52a0", None))
        self.actionCamera1.setText(QCoreApplication.translate("MainWindow", u"Camera1", None))
        self.actionCamera2.setText(QCoreApplication.translate("MainWindow", u"Camera2", None))
        self.actionStart.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.actionStop.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
        self.actionRescan.setText(QCoreApplication.translate("MainWindow", u"Rescan", None))
        self.actionAudio1.setText(QCoreApplication.translate("MainWindow", u"Audio1", None))
        self.actionAudio2.setText(QCoreApplication.translate("MainWindow", u"Audio2", None))
        self.actionRescan_2.setText(QCoreApplication.translate("MainWindow", u"Rescan", None))
        self.actionMute.setText(QCoreApplication.translate("MainWindow", u"Mute", None))
        self.actionSettings.setText(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.lblCameraPlayer.setText("")
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"\u91c7\u96c6\u53c2\u6570", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"\u89c6\u9891:", None))
        self.btnCameraOpt.setText(QCoreApplication.translate("MainWindow", u"\u505c\u6b62", None))
        self.btnRescan.setText(QCoreApplication.translate("MainWindow", u"\u91cd\u65b0\u68c0\u7d22", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"FPS:", None))
        self.cbxFps.setItemText(0, QCoreApplication.translate("MainWindow", u"10", None))
        self.cbxFps.setItemText(1, QCoreApplication.translate("MainWindow", u"15", None))
        self.cbxFps.setItemText(2, QCoreApplication.translate("MainWindow", u"20", None))
        self.cbxFps.setItemText(3, QCoreApplication.translate("MainWindow", u"30", None))
        self.cbxFps.setItemText(4, QCoreApplication.translate("MainWindow", u"45", None))
        self.cbxFps.setItemText(5, QCoreApplication.translate("MainWindow", u"60", None))

        self.cbxFps.setCurrentText(QCoreApplication.translate("MainWindow", u"10", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"\u97f3\u9891:", None))
        self.chbMute.setText(QCoreApplication.translate("MainWindow", u"\u9759\u97f3", None))
    # retranslateUi

