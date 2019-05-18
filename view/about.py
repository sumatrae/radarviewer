from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread
from PyQt5.QtGui import QIcon, QPalette, QImage,QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox
from PyQt5.uic import loadUi

import cv2

class AboutDialog(QDialog):
    def __init__(self, *args):
        super(AboutDialog, self).__init__(*args)
        self.serial_setting_dialog = loadUi("./ui/about.ui", self)
        self.serial_setting_dialog.label.setText(str("< font>成都多普勒科技有限公司 Copyright&copy;2019</font>"))

