import configparser
import gc
import os
import re
import sys

from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread
from PyQt5.QtGui import QIcon, QPalette, QImage,QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox
from PyQt5.uic import loadUi

from camera import Camera
from camera import CameraManager

import cv2
import device

class CameraSettingDialog(QDialog):
    def __init__(self, *args):
        super(CameraSettingDialog, self).__init__(*args)
        self.camera_setting_dialog = loadUi("camera_setting.ui", self)

        device_list = CameraManager().list_cameras()
        index = 0

        # for name in device_list:
        #     print(str(index) + ': ' + name)
        #     index += 1

        self.camera_setting_dialog.comboBox_camera.addItems(device_list)

    def get_current_camera_cfg(self):
        camera_id = self.camera_setting_dialog.comboBox_camera.currentIndex()

        #get cfg

        #show cfg

    #def setting back to main

class A():
    def __init__(self):
        device_list = CameraManager().list_cameras()
        index = 0

        for name in device_list:
            print(str(index) + ': ' + name)
            index += 1

