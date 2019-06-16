import configparser
import gc
import os
import re
import sys

import random

from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread
from PyQt5.QtGui import QIcon, QPalette, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox, QGridLayout
from PyQt5.uic import loadUi

import matplotlib
matplotlib.use("Qt5Agg")  # 声明使用QT5
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from camera import Camera
from camera import CameraManager

import cv2 as cv

import threading
from collections import deque
import camera_setting
import serial_setting
import about

from PIL import Image
from processing import *

from radar import *

#棋盘格模板规格
w = 11
h = 8

#创建一个matplotlib图形绘制类
class MyFigure(FigureCanvas):
    def __init__(self,width=3, height=2, dpi=100):
        #第一步：创建一个创建Figure
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        #第二步：在父类中激活Figure窗口
        super(MyFigure,self).__init__(self.fig) #此句必不可少，否则不能显示图形
        #第三步：创建一个子图，用于绘制图形用，111表示子图编号，如matlab的subplot(1,1,1)
        #self.axes = self.fig.add_subplot(111)
        self.axes = self.fig.gca()


class Radar_Viewer(QMainWindow):
    def __init__(self, *args):
        super(Radar_Viewer, self).__init__(*args)

        self.radar_viewer = loadUi("./ui/radar_viewer.ui", self)
        self.radar_viewer.tab_widget.setCurrentIndex(0)

        self.cam_manager = CameraManager()
        self.radar_viewer.actionCamera_Setting.triggered.connect(self.start_camera_setting_dialog)

        self.uart_cfg = UartConfig("COM0")
        self.radar_viewer.actionRadar_Setting.triggered.connect(self.start_serial_setting_dialog)

        self.radar_viewer.actionAbout.triggered.connect(self.start_about_dialog)

        self.frame_update_timer = QTimer(self)
        self.frame_update_timer.timeout.connect(self.update)
        self.frame_update_timer.start((int)(1000.0 / self.cam_manager.framerate))

        self.detector = YOLO()

        self.criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        self.F = MyFigure(width=6, height=4, dpi=100)
        # self.F.plotsin()
        self.plot_scatter()

        self.gridlayout = QGridLayout(self.radar_viewer.groupBox_radar)  # 继承容器groupBox
        self.gridlayout.addWidget(self.F, 0, 1)

        self.video_width = 1150
        self.video_height = 650


    def plot_scatter(self):
        y_max = 100
        y_min = 0
        x_max = 10
        x_min = -10
        point_num = 10

        rect = plt.Rectangle((-5, 5), 10, 40, linewidth=1, edgecolor='r', facecolor='r')
        rect.set_alpha(0.3)
        self.F.axes.add_patch(rect)

        self.F.axes.scatter(np.random.uniform(x_min,x_max,point_num), np.random.uniform(y_min,y_max,point_num))
        self.F.axes.axis([x_min, x_max, y_min, y_max])

        self.F.axes.grid(color='deepskyblue', linestyle='dashed', linewidth=1,alpha=0.3)

        self.F.axes.spines['top'].set_visible(False)  # 去掉上边框
        self.F.axes.spines['right'].set_visible(False)  # 去掉右边框
        self.F.axes.spines['left'].set_position(('axes', 0.5))
        self.F.fig.tight_layout()
        #self.F.axes.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        #self.F.axes.yaxis.set_ticks_position('left')

        #self.F.fig.suptitle("scatter")


    def start_camera_setting_dialog(self):
        self.camera_setting_dialog = camera_setting.CameraSettingDialog(self.cam_manager)
        self.camera_setting_dialog.camera_setting_signal.connect(self.update_camera_info)

        self.camera_setting_dialog.show()

    def start_serial_setting_dialog(self):
        try:
            self.serial_setting_dialog = serial_setting.SerialSettingDialog(self.uart_cfg)
            self.serial_setting_dialog.serial_setting_signal.connect(self.update_uart_info)
            self.serial_setting_dialog.show()
        except Exception as e:
            print(e)

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

    def update_uart_info(self, uart_config_msg):
        self.uart_cfg = uart_config_msg
        #pass


    # def update(self):
    #     ret, frame = self.cam_manager.cam.take_photo()
    #     if ret == True:
    #         frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    #
    #         image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
    #
    #         pixmap = QPixmap.fromImage(image)
    #
    #         scaled_pixmap = pixmap.scaled(1.5 * frame.shape[1], 1.5 * frame.shape[0],
    #                                       aspectRatioMode=Qt.KeepAspectRatioByExpanding,
    #                                       transformMode=Qt.SmoothTransformation)
    #
    #         self.radar_viewer.label_video.setPixmap(scaled_pixmap)

    def update(self):
        ret, frame = self.cam_manager.cam.take_photo()
        if ret == True:
            #pass
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

            # 找到棋盘格角点
            # ret, corners = cv.findChessboardCorners(gray, (w, h), None)
            # if ret == True:
            #     cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
            #     cv.drawChessboardCorners(frame, (w, h), corners, ret)

            imagePoints = cv.projectPoints(objectPoints, rvec, tvec, mtx, dist)

            frame1 = Image.fromarray(frame)
            self.detector.detect_image(frame1)
            frame = np.asarray(frame1)

            point = np.array(imagePoints[0][0, 0, :]).astype(int)
            print(point)
            cv.circle(frame, tuple(point), 2, (0,0,255), 4)

            cv.rectangle(frame,tuple(point - 20), tuple(point + 20),(0,255,0),3)
            cv.putText(frame, "({},{}),1.2m/s".format(objectPoints[0,0]/1000,objectPoints[0,2]/1000),
                       (point[0]-20,point[1]-25), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)



            self.frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            self.image = QImage(frame.data, frame.shape[1], self.frame.shape[0], QImage.Format_RGB888)

            self.pixmap = QPixmap.fromImage( self.image)

            self.scaled_pixmap = self.pixmap.scaled(self.video_width, self.video_height,
                                          aspectRatioMode=Qt.KeepAspectRatioByExpanding,
                                          transformMode=Qt.SmoothTransformation)

            self.radar_viewer.label_video.setPixmap(self.scaled_pixmap)

    def resizeEvent(self, event):
        # self.scaled_pixmap = self.pixmap.scaled(self.radar_viewer.label_video.width(),
        #                                         self.radar_viewer.label_video.height(),
        #                                         aspectRatioMode=Qt.KeepAspectRatioByExpanding,
        #                                         transformMode=Qt.SmoothTransformation)
        # self.radar_viewer.label_video.setPixmap(self.scaled_pixmap)
        print("resize event")





app = QApplication(sys.argv)
main_window = Radar_Viewer()
main_window.show()
sys.exit(app.exec_())
