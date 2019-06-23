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
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QRegExpValidator
# 导入Qt正则模块
from PyQt5.QtCore import QRegExp

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
import time

from PIL import Image
from processing import *

from radar import *
import glob
from collections import deque

# 棋盘格模板规格
CHESSBOARD_W_NUM = 11
CHESSBOARD_H_NUM = 8
CRITERIA = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
IMG_PATH = "../temp"

IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 640


class QtFigure(FigureCanvas):
    def __init__(self, width=3, height=2, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(QtFigure, self).__init__(self.fig)  # 此句必不可少，否则不能显示图形
        self.axes = self.fig.gca()


class Radar_Viewer(QMainWindow):
    def __init__(self, *args):
        super(Radar_Viewer, self).__init__(*args)

        # load main ui
        self.radar_viewer = loadUi("./ui/radar_viewer.ui", self)
        self.radar_viewer.tab_widget.setCurrentIndex(0)

        self.init_manu_bar()
        self.load_radar_axis()

        self.radar_max_x_abs = 50
        self.radar_max_y_abs = 200
        self.radar_y_max = self.radar_max_y_abs
        self.radar_y_min = 0
        self.radar_x_max = self.radar_max_x_abs
        self.radar_x_min = -self.radar_max_x_abs
        self.handle_radar_capture_area_setting()

        # init video
        self.video_width = 1200
        self.video_height = 540
        self.detector = YOLO()
        self.detector_enable = False

        self.init_main_ui_setting()
        self.init_timers()

        self.img_queue = deque()
        self.current_image_index = -1
        self.init_img_queue()

        self.radar_viewer.pushButton_pre.clicked.connect(self.pre_image)
        self.radar_viewer.pushButton_next.clicked.connect(self.next_image)

        # self.showFullScreen()
        # self.showMaximized()

    def init_manu_bar(self):
        # init menu
        self.cam_manager = CameraManager()
        self.radar_viewer.actionCamera_Setting.triggered.connect(self.start_camera_setting_dialog)

        self.uart_cfg = UartConfig("COM0")
        self.radar_viewer.actionRadar_Setting.triggered.connect(self.start_serial_setting_dialog)
        self.radar_viewer.actionAbout.triggered.connect(self.start_about_dialog)

    def load_radar_axis(self):
        # load radar axis
        self.qtfig = QtFigure(width=6, height=4, dpi=100)
        # self.plot_scatter()
        self.gridlayout = QGridLayout(self.radar_viewer.groupBox_radar)
        self.gridlayout.addWidget(self.qtfig)

        self.scatter_collection = None

    def init_main_ui_setting(self):
        # init setting
        self.radar_viewer.checkBox_detector_switch.stateChanged.connect(self.set_cv_detector)
        self.radar_viewer.checkBox_cv_trigger.stateChanged.connect(self.set_cv_trigger)
        self.radar_viewer.checkBox_radar_trigger.stateChanged.connect(self.set_radar_trigger)
        self.radar_viewer.checkBox_save_picture_auto.stateChanged.connect(self.set_save_picture_auto)

        re_float = QRegExp("(-*[1-9][0-9]{0,2}|0)([\.][0-9]{1,2})*")
        re_validato = QRegExpValidator(re_float, self)  # 实例化正则验证器
        self.radar_viewer.lineEdit_radar_startx.setValidator(re_validato)  # 设置验证
        self.radar_viewer.lineEdit_radar_startx.move(50, 90)
        self.radar_viewer.lineEdit_radar_starty.setValidator(re_validato)  # 设置验证
        self.radar_viewer.lineEdit_radar_starty.move(50, 90)
        self.radar_viewer.lineEdit_radar_capture_width.setValidator(re_validato)  # 设置验证
        self.radar_viewer.lineEdit_radar_capture_width.move(50, 90)
        self.radar_viewer.lineEdit_radar_capture_deepth.setValidator(re_validato)  # 设置验证
        self.radar_viewer.lineEdit_radar_capture_deepth.move(50, 90)

        self.radar_viewer.lineEdit_radar_startx.returnPressed.connect(self.handle_radar_capture_area_setting)
        self.radar_viewer.lineEdit_radar_starty.returnPressed.connect(self.handle_radar_capture_area_setting)
        self.radar_viewer.lineEdit_radar_capture_width.returnPressed.connect(self.handle_radar_capture_area_setting)
        self.radar_viewer.lineEdit_radar_capture_deepth.returnPressed.connect(self.handle_radar_capture_area_setting)

        int_validato = QIntValidator(1, 999999, self)
        self.radar_viewer.lineEdit_image_capture_period.setValidator(int_validato)  # 设置验证
        self.radar_viewer.lineEdit_image_capture_period.move(50, 90)
        self.radar_viewer.lineEdit_image_capture_period.returnPressed.connect(self.set_image_capture_period)

        self.radar_viewer.horizontalSlider_video_brightness.setRange(0, 200)
        self.radar_viewer.horizontalSlider_video_contrast.setRange(0, 100)
        self.radar_viewer.horizontalSlider_video_brightness.setValue(self.cam_manager.brightness)
        self.radar_viewer.horizontalSlider_video_contrast.setValue(self.cam_manager.contrast)
        self.radar_viewer.horizontalSlider_video_brightness.valueChanged.connect(self.set_video_brightness)
        self.radar_viewer.horizontalSlider_video_contrast.valueChanged.connect(self.set_video_contrast)

        self.cv_trigger_enable = False
        self.radar_trigger_enable = False

    def set_video_brightness(self):
        self.cam_manager.brightness = self.radar_viewer.horizontalSlider_video_brightness.value()
        self.cam_manager.update_camera_info(self.cam_manager.id)

    def set_video_contrast(self):
        self.cam_manager.contrast = self.radar_viewer.horizontalSlider_video_contrast.value()
        self.cam_manager.update_camera_info(self.cam_manager.id)

    def init_timers(self):
        # set video update timer
        self.frame_update_timer = QTimer(self)
        self.frame_update_timer.timeout.connect(self.update_video)
        self.frame_update_timer.start((int)(1000.0 / self.cam_manager.framerate))

        self.radar_update_timer = QTimer(self)
        self.radar_update_timer.timeout.connect(self.update_radar)
        self.radar_update_timer.start(1000)

    def set_image_capture_period(self):
        print(self.radar_viewer.lineEdit_image_capture_period.text())

    def handle_radar_capture_area_setting(self):
        radar_startx = float(self.radar_viewer.lineEdit_radar_startx.text())
        radar_starty = float(self.radar_viewer.lineEdit_radar_starty.text())
        radar_capture_width = float(self.radar_viewer.lineEdit_radar_capture_width.text())
        radar_capture_deepth = float(self.radar_viewer.lineEdit_radar_capture_deepth.text())

        if (abs(radar_startx) < self.radar_max_x_abs or -radar_startx == self.radar_max_x_abs) \
                and 0 <= radar_starty < self.radar_y_max \
                and radar_startx + radar_capture_width <= self.radar_max_x_abs \
                and radar_starty + radar_capture_deepth <= self.radar_y_max \
                and radar_capture_width > 0 \
                and radar_capture_deepth > 0:
            self.radar_startx = radar_startx
            self.radar_starty = radar_starty
            self.radar_capture_width = radar_capture_width
            self.radar_capture_deepth = radar_capture_deepth

            self.delete_capture_area()
            self.draw_capture_area()
        else:
            print("invalid area")

    def draw_axis(self):
        self.qtfig.axes.axis([self.radar_x_min, self.radar_x_max, self.radar_y_min, self.radar_y_max])
        self.qtfig.axes.grid(color='deepskyblue', linestyle='dashed', linewidth=1, alpha=0.3)
        self.qtfig.axes.spines['top'].set_visible(False)  # 去掉上边框
        self.qtfig.axes.spines['right'].set_visible(False)  # 去掉右边框
        self.qtfig.axes.spines['left'].set_position(('axes', 0.5))
        self.qtfig.fig.tight_layout()

    def draw_capture_area(self):
        self.rect = plt.Rectangle((self.radar_startx, self.radar_starty), self.radar_capture_width,
                                  self.radar_capture_deepth,
                                  linewidth=1, edgecolor='r', facecolor='r')
        self.rect.set_alpha(0.3)
        self.qtfig.axes.add_patch(self.rect)

    def delete_capture_area(self):
        [p.remove() for p in reversed(self.qtfig.axes.patches)]

    def plot_scatter(self):
        point_num = 10

        # self.qtfig.fig.canvas.draw_idle()
        # if self.scatter_collection:
        #     self.scatter_collection.remove()

        # self.draw_axis()
        if self.scatter_collection:
            self.scatter_collection.remove()
            self.qtfig.fig.canvas.draw_idle()

        self.draw_axis()

        self.scatter_collection = self.qtfig.axes.scatter(
            np.random.uniform(self.radar_x_min, self.radar_x_max, point_num),
            np.random.uniform(self.radar_y_min, self.radar_y_max, point_num))

    def update_radar(self):
        # if self.scatter_collection:
        #     self.scatter_collection.remove()
        plt.clf()
        self.plot_scatter()

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

        self.radar_viewer.horizontalSlider_video_brightness.setValue(self.cam_manager.brightness)
        self.radar_viewer.horizontalSlider_video_contrast.setValue(self.cam_manager.contrast)

        self.frame_update_timer.start((int)(1000.0 / self.cam_manager.framerate))

    def update_uart_info(self, uart_config_msg):
        self.uart_cfg = uart_config_msg

    def update_video(self):
        ret, frame = self.cam_manager.cam.take_photo()
        if ret == True:
            # gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            # 找到棋盘格角点
            # ret, corners = cv.findChessboardCorners(gray, (CHESSBOARD_W_NUM, CHESSBOARD_H_NUM), None)
            # if ret == True:
            #     cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), CRITERIA)
            #     cv.drawChessboardCorners(frame, (w, h), corners, ret)

            imagePoints = cv.projectPoints(objectPoints, rvec, tvec, mtx, dist)

            self.exist_person = False
            if self.detector_enable:
                frame1 = Image.fromarray(frame)
                _, self.exist_person = self.detector.detect_image(frame1)
                frame = np.asarray(frame1)

            point = np.array(imagePoints[0][0, 0, :]).astype(int)
            cv.circle(frame, tuple(point), 2, (0, 0, 255), 4)

            cv.rectangle(frame, tuple(point - 20), tuple(point + 20), (0, 255, 0), 3)
            cv.putText(frame, "({},{}),1.2m/s".format(objectPoints[0, 0] / 1000, objectPoints[0, 2] / 1000),
                       (point[0] - 20, point[1] - 25), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            self.frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            # print(type(self.frame))
            if self.cv_trigger_enable:
                if self.exist_person:
                    self.save_img(self.frame)

            if self.radar_trigger_enable and not self.exist_person:
                if self.obstacle_in_area:
                    self.save_img(self.frame)

            self.image = QImage(self.frame.data, self.frame.shape[1], self.frame.shape[0], QImage.Format_RGB888)
            self.pixmap = QPixmap.fromImage(self.image)
            self.scaled_pixmap = self.pixmap.scaled(self.video_width, self.video_height,
                                                    aspectRatioMode=Qt.KeepAspectRatioByExpanding,
                                                    transformMode=Qt.SmoothTransformation)
            self.radar_viewer.label_video.setPixmap(self.scaled_pixmap)

    def set_cv_detector(self):
        if self.radar_viewer.checkBox_detector_switch.checkState() == Qt.Checked:
            self.detector_enable = True
        elif self.radar_viewer.checkBox_detector_switch.checkState() == Qt.Unchecked:
            self.detector_enable = False

    def set_cv_trigger(self):
        if self.radar_viewer.checkBox_cv_trigger.checkState() == Qt.Checked:
            self.cv_trigger_enable = True
        elif self.radar_viewer.checkBox_cv_trigger.checkState() == Qt.Unchecked:
            self.cv_trigger_enable = False

    def set_radar_trigger(self):
        if self.radar_viewer.checkBox_radar_trigger.checkState() == Qt.Checked:
            self.radar_trigger_enable = True
        elif self.radar_viewer.checkBox_radar_trigger.checkState() == Qt.Unchecked:
            self.radar_trigger_enable = False

    def set_save_picture_auto(self):
        if self.radar_viewer.checkBox_save_picture_auto.checkState() == Qt.Checked:
            self.save_picture_auto = True
        elif self.radar_viewer.checkBox_save_picture_auto.checkState() == Qt.Unchecked:
            self.save_picture_auto = False

    def resizeEvent(self, event):
        # self.scaled_pixmap = self.pixmap.scaled(self.radar_viewer.label_video.width(),
        #                                         self.radar_viewer.label_video.height(),
        #                                         aspectRatioMode=Qt.KeepAspectRatioByExpanding,
        #                                         transformMode=Qt.SmoothTransformation)
        # self.radar_viewer.label_video.setPixmap(self.scaled_pixmap)
        print("resize event")

    def save_img(self, img):
        filename = time.ctime().replace(":", " ")
        img_name = "{}\\{}.jpg".format(os.path.realpath(IMG_PATH), filename)
        if cv.imwrite(img_name, img):
            self.img_queue.append(img_name)
            self.show_image(self.current_image_index)

    def show_newest_img(self):
        newest_img = self.img_queue[-1]
        frame = cv.imread(newest_img)

        # self.radar_viewer.tab_image.label_image = 0

    def show_image(self, index):
        try:
            if len(self.img_queue):
                newest_img = self.img_queue[index]
                frame = cv.imread(newest_img, cv.COLOR_BGR2RGB)
                image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)
                scaled_pixmap = pixmap.scaled(IMAGE_WIDTH, IMAGE_HEIGHT,
                                              aspectRatioMode=Qt.KeepAspectRatioByExpanding,
                                              transformMode=Qt.SmoothTransformation)
                self.radar_viewer.label_photo.setPixmap(scaled_pixmap)
        except Exception as e:
            print(e)

    def pre_image(self):
        if len(self.img_queue):
            self.current_image_index = -1 if self.current_image_index + 1 < -len(
                self.img_queue) else self.current_image_index - 1
            self.show_image(self.current_image_index)

    def next_image(self):
        if len(self.img_queue):
            self.current_image_index = -len(
                self.img_queue) if self.current_image_index + 1 > -1 else self.current_image_index + 1
            self.show_image(self.current_image_index)

    def init_img_queue(self):

        imgs_list = glob.glob(IMG_PATH + "/*.jpg")
        imgs_list.sort(key=lambda f: os.path.getctime(f))
        self.img_queue.clear()
        self.img_queue.extend(imgs_list)
        self.show_image(self.current_image_index)


app = QApplication(sys.argv)
main_window = Radar_Viewer()
main_window.show()
sys.exit(app.exec_())
