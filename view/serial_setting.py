import configparser
import gc
import os
import re
import sys

from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread
from PyQt5.QtGui import QIcon, QPalette, QImage,QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox
from PyQt5.uic import loadUi

import cv2

class SerialSettingDialog(QDialog):
    def __init__(self, *args):
        super(SerialSettingDialog, self).__init__(*args)
        self.serial_setting_dialog = loadUi("./ui/serial_setting.ui", self)


