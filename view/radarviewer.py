import configparser
import gc
import os
import re
import sys

from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread
from PyQt5.QtGui import QIcon, QPalette, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox
from PyQt5.uic import loadUi

from camera import Camera
from camera import CameraManager

import cv2 as cv

import threading
from collections import deque
import camera_setting
import serial_setting
import about


class Radar_Viewer(QMainWindow):
    def __init__(self, *args):
        super(Radar_Viewer, self).__init__(*args)

        self.radar_viewer = loadUi("./ui/radar_viewer.ui", self)
        self.radar_viewer.tab_widget.setCurrentIndex(0)

        self.cam_manager = CameraManager()
        self.radar_viewer.actionCamera_Setting.triggered.connect(self.start_camera_setting_dialog)

        self.radar_viewer.actionRadar_Setting.triggered.connect(self.start_serial_setting_dialog)

        self.radar_viewer.actionAbout.triggered.connect(self.start_about_dialog)

        self.frame_update_timer = QTimer(self)
        self.frame_update_timer.timeout.connect(self.update)
        self.frame_update_timer.start((int)(1000.0 / self.cam_manager.framerate))

    def start_camera_setting_dialog(self):
        self.camera_setting_dialog = camera_setting.CameraSettingDialog(self.cam_manager)
        self.camera_setting_dialog.camera_setting_signal.connect(self.update_camera_info)

        self.camera_setting_dialog.show()

    def start_serial_setting_dialog(self):
        self.serial_setting_dialog = serial_setting.SerialSettingDialog()

        self.serial_setting_dialog.show()

    def start_about_dialog(self):
        self.about_dialog = about.AboutDialog()
        self.about_dialog.show()

    def update_camera_info(self, camera_config_msg):
        self.frame_update_timer.stop()
        self.cam_manager.framerate = camera_config_msg.framerate
        self.cam_manager.resolution[0] = camera_config_msg.resolution[0]
        self.cam_manager.resolution[1] = camera_config_msg.resolution[1]
        self.cam_manager.brightness = camera_config_msg.brightness
        self.cam_manager.contrast = camera_config_msg.contrast
        self.cam_manager.gain = camera_config_msg.gain
        self.cam_manager.update_camera_info(camera_config_msg.id)
        self.frame_update_timer.start((int)(1000.0 / self.cam_manager.framerate))

    def update(self):
        ret, frame = self.cam_manager.cam.take_photo()
        if ret == True:
            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)

            pixmap = QPixmap.fromImage(image)

            scaled_pixmap = pixmap.scaled(2 * frame.shape[1], 2 * frame.shape[0],
                                          aspectRatioMode=Qt.KeepAspectRatioByExpanding,
                                          transformMode=Qt.SmoothTransformation)

            self.radar_viewer.label_video.setPixmap(scaled_pixmap)


app = QApplication(sys.argv)
main_window = Radar_Viewer()
main_window.show()
sys.exit(app.exec_())
