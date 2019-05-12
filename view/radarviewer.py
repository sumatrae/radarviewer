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

import cv2 as cv

import threading
from collections import deque
import camera_setting

class Radar_Viewer(QMainWindow):
    def __init__(self, *args):
        super(Radar_Viewer, self).__init__(*args)

        self.radar_viewer = loadUi("./ui/radar_viewer.ui", self)
        self.radar_viewer.tab_widget.setCurrentIndex(0)


        self.cam_manager = CameraManager()
        self.cam = self.cam_manager.get_camera_instance()

        self.camera_setting_dialog = camera_setting.CameraSettingDialog(self.cam_manager)
        self.radar_viewer.actionCamera_Setting.triggered.connect(self.start_camera_setting_dialog)


        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        framerate = 30
        self.timer.start((int)(1000.0/framerate))

    def start_camera_setting_dialog(self):
        self.camera_setting_dialog.show()


    def update(self):
            _, frame = self.cam.take_photo()
            frame = cv.cvtColor(frame,cv.COLOR_BGR2RGB)
            image = QImage(frame.data, frame.shape[1],frame.shape[0],QImage.Format_RGB888)

            pixmap = QPixmap.fromImage(image)

            scaled_pixmap = pixmap.scaled(1.5*frame.shape[1],1.5*frame.shape[0],
                                          aspectRatioMode = Qt.KeepAspectRatioByExpanding,
                                          transformMode = Qt.SmoothTransformation)

            self.radar_viewer.label_video.setPixmap(scaled_pixmap)

app = QApplication(sys.argv)
widget = Radar_Viewer()
widget.show()
sys.exit(app.exec_())
