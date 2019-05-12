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

class CameraSettingDialog(QDialog):
    def __init__(self,camera_manager, *args):
        super(CameraSettingDialog, self).__init__(*args)
        self.camera_setting_dialog = loadUi("./ui/camera_setting.ui", self)
        self.camera_setting_dialog.comboBox_camera.addItems(camera_manager.camera_list)
        self.camera_setting_dialog.lineEdit_framerate.setText(str(camera_manager.framerate))
        self.camera_setting_dialog.lineEdit_width.setText(str(camera_manager.resolution[0]))
        self.camera_setting_dialog.lineEdit_height.setText(str(camera_manager.resolution[1]))
        self.camera_setting_dialog.lineEdit_brightness.setText(str(camera_manager.brightness))
        self.camera_setting_dialog.lineEdit_contrast.setText(str(camera_manager.contrast))
        self.camera_setting_dialog.lineEdit_gain.setText(str(camera_manager.gain))

    def get_current_camera_cfg(self):
        camera_id = self.camera_setting_dialog.comboBox_camera.currentIndex()

        #get cfg

        #show cfg

    #def setting back to main

