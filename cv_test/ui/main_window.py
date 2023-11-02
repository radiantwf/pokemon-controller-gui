import cv2
from PySide6 import QtWidgets, QtGui
from PySide6.QtUiTools import loadUiType
Ui_MainWindow, QMainWindowBase = loadUiType("cv_test/ui/cv_test_form.ui")


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)


    def setupUi(self):
        Ui_MainWindow.setupUi(self, self)
