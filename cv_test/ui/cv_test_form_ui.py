# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cv_test_form.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
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
from PySide6.QtWidgets import (QApplication, QFrame, QGroupBox, QLabel,
    QMainWindow, QPushButton, QSizePolicy, QStatusBar,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1340, 900)
        MainWindow.setMinimumSize(QSize(1340, 900))
        MainWindow.setMaximumSize(QSize(1340, 900))
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
        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(20, 10, 640, 421))
        self.lblCameraFrame_1 = QLabel(self.groupBox)
        self.lblCameraFrame_1.setObjectName(u"lblCameraFrame_1")
        self.lblCameraFrame_1.setGeometry(QRect(0, 20, 640, 360))
        self.lblCameraFrame_1.setFrameShape(QFrame.StyledPanel)
        self.lblCameraFrame_1.setFrameShadow(QFrame.Plain)
        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(680, 10, 640, 420))
        self.lblCameraFrame_2 = QLabel(self.groupBox_2)
        self.lblCameraFrame_2.setObjectName(u"lblCameraFrame_2")
        self.lblCameraFrame_2.setGeometry(QRect(0, 20, 640, 360))
        self.lblCameraFrame_2.setFrameShape(QFrame.StyledPanel)
        self.lblCameraFrame_2.setFrameShadow(QFrame.Plain)
        self.btn_process_1 = QPushButton(self.groupBox_2)
        self.btn_process_1.setObjectName(u"btn_process_1")
        self.btn_process_1.setGeometry(QRect(530, 385, 100, 32))
        self.groupBox_3 = QGroupBox(self.centralwidget)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setGeometry(QRect(20, 440, 640, 420))
        self.lblCameraFrame_3 = QLabel(self.groupBox_3)
        self.lblCameraFrame_3.setObjectName(u"lblCameraFrame_3")
        self.lblCameraFrame_3.setGeometry(QRect(0, 20, 640, 360))
        self.lblCameraFrame_3.setFrameShape(QFrame.StyledPanel)
        self.lblCameraFrame_3.setFrameShadow(QFrame.Plain)
        self.btn_process_2 = QPushButton(self.groupBox_3)
        self.btn_process_2.setObjectName(u"btn_process_2")
        self.btn_process_2.setGeometry(QRect(530, 385, 100, 32))
        self.groupBox_4 = QGroupBox(self.centralwidget)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.groupBox_4.setGeometry(QRect(680, 440, 640, 420))
        self.lblCameraFrame_4 = QLabel(self.groupBox_4)
        self.lblCameraFrame_4.setObjectName(u"lblCameraFrame_4")
        self.lblCameraFrame_4.setGeometry(QRect(0, 20, 640, 360))
        self.lblCameraFrame_4.setFrameShape(QFrame.StyledPanel)
        self.lblCameraFrame_4.setFrameShadow(QFrame.Plain)
        self.btn_process_3 = QPushButton(self.groupBox_4)
        self.btn_process_3.setObjectName(u"btn_process_3")
        self.btn_process_3.setGeometry(QRect(530, 385, 100, 32))
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u56fe\u50cf\u5904\u7406\u6d4b\u8bd5", None))
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
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"\u539f\u89c6\u9891", None))
        self.lblCameraFrame_1.setText("")
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"\u89c6\u9891\u5904\u74061", None))
        self.lblCameraFrame_2.setText("")
        self.btn_process_1.setText(QCoreApplication.translate("MainWindow", u"\u53c2\u6570\u4fee\u6539", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"\u89c6\u9891\u5904\u74062", None))
        self.lblCameraFrame_3.setText("")
        self.btn_process_2.setText(QCoreApplication.translate("MainWindow", u"\u53c2\u6570\u4fee\u6539", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"\u89c6\u9891\u5904\u74063", None))
        self.lblCameraFrame_4.setText("")
        self.btn_process_3.setText(QCoreApplication.translate("MainWindow", u"\u53c2\u6570\u4fee\u6539", None))
    # retranslateUi

