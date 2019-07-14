import os
import glob
import sys
from collections import deque

import cv2 as cv
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QRegExp, Qt, QTimer
from PyQt5.QtGui import (QImage, QIntValidator, QPixmap, QRegExpValidator)
from PyQt5.QtWidgets import (QApplication, QGridLayout, QMainWindow)
from PyQt5.uic import loadUi

import about
import camera_setting
import radar
import serial_setting
from camera import (CameraManager, CameraThread)
from processing import DetectorThread
from radar import *

matplotlib.use("Qt5Agg")  # 声明使用QT5

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
        super(QtFigure, self).__init__(self.fig)
        self.axes = self.fig.gca()


class Monitor:
    startx = -5
    starty = 0
    width = 10
    deepth = 10


class Axis:
    radar_max_x_abs = 10
    radar_max_y_abs = 80

    def __init__(self):
        self.radar_y_max = self.radar_max_y_abs
        self.radar_y_min = 0
        self.radar_x_max = self.radar_max_x_abs
        self.radar_x_min = -self.radar_max_x_abs


class Radar_Viewer(QMainWindow):
    def __init__(self, *args):
        super(Radar_Viewer, self).__init__(*args)
        self.cam_manager = CameraManager()
        self.uart_cfg = UartConfig("COM0")

        # load main ui
        self.radar_viewer = loadUi("./ui/radar_viewer.ui", self)
        self.init_menu()
        self.init_main_page()
        self.init_image_page()

        # initial threads and timers
        self.init_threads()
        self.init_timers()
        # self.showFullScreen()
        # self.showMaximized()

    def init_menu(self):
        # init menu
        self.radar_viewer.actionCamera_Setting.triggered.connect(self.start_camera_setting_dialog)
        self.radar_viewer.actionRadar_Setting.triggered.connect(self.start_serial_setting_dialog)
        self.radar_viewer.actionAbout.triggered.connect(self.start_about_dialog)

    def init_radar_axis_para(self):
        self.radar_max_x_abs = 10
        self.radar_max_y_abs = 80
        self.radar_y_max = self.radar_max_y_abs
        self.radar_y_min = 0
        self.radar_x_max = self.radar_max_x_abs
        self.radar_x_min = -self.radar_max_x_abs

        self.initial_startx = -5
        self.initial_starty = 0
        self.initial_width = 10
        self.initial_deepth = 10

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

    def handle_radar_capture_area_setting(self):
        self.cv_trigger_enable = False
        self.radar_trigger_enable = False
        self.obstacle_in_area = False

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

    def load_radar_axis(self):
        self.init_radar_axis_para()
        self.qtfig = QtFigure(width=6, height=4, dpi=100)
        self.gridlayout = QGridLayout(self.radar_viewer.groupBox_radar)
        self.gridlayout.addWidget(self.qtfig)
        self.draw_axis()
        self.scatter_collection = None
        self.texts = None
        self.handle_radar_capture_area_setting()

    def set_cv_detector(self):
        if self.radar_viewer.checkBox_detector_switch.checkState() == Qt.Checked:
            self.detector_enable = True
            self.detector_thread.set_enable(True)

        elif self.radar_viewer.checkBox_detector_switch.checkState() == Qt.Unchecked:
            self.detector_enable = False
            self.detector_thread.set_enable(False)

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

    def init_main_ui_setting(self):
        self.detector_enable = False
        self.set_cv_trigger()
        self.set_radar_trigger()

        self.radar_viewer.checkBox_detector_switch.setEnabled(False)


        # init setting
        self.radar_viewer.checkBox_detector_switch.stateChanged.connect(self.set_cv_detector)
        self.radar_viewer.checkBox_cv_trigger.stateChanged.connect(self.set_cv_trigger)
        self.radar_viewer.checkBox_radar_trigger.stateChanged.connect(self.set_radar_trigger)
        # self.radar_viewer.checkBox_save_picture_auto.stateChanged.connect(self.set_save_picture_auto)

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

        self.radar_viewer.lineEdit_radar_startx.setText(str(self.initial_startx))
        self.radar_viewer.lineEdit_radar_starty.setText(str(self.initial_starty))
        self.radar_viewer.lineEdit_radar_capture_width.setText(str(self.initial_width))
        self.radar_viewer.lineEdit_radar_capture_deepth.setText(str(self.initial_deepth))

        self.radar_viewer.lineEdit_radar_startx.returnPressed.connect(self.handle_radar_capture_area_setting)
        self.radar_viewer.lineEdit_radar_starty.returnPressed.connect(self.handle_radar_capture_area_setting)
        self.radar_viewer.lineEdit_radar_capture_width.returnPressed.connect(self.handle_radar_capture_area_setting)
        self.radar_viewer.lineEdit_radar_capture_deepth.returnPressed.connect(self.handle_radar_capture_area_setting)

        self.radar_viewer.horizontalSlider_video_brightness.setRange(0, 200)
        self.radar_viewer.horizontalSlider_video_contrast.setRange(0, 100)
        self.radar_viewer.horizontalSlider_video_brightness.setValue(self.cam_manager.brightness)
        self.radar_viewer.horizontalSlider_video_contrast.setValue(self.cam_manager.contrast)
        self.radar_viewer.horizontalSlider_video_brightness.valueChanged.connect(self.set_video_brightness)
        self.radar_viewer.horizontalSlider_video_contrast.valueChanged.connect(self.set_video_contrast)

    def init_main_page(self):
        self.radar_viewer.tab_widget.setCurrentIndex(0)
        self.load_radar_axis()
        self.init_main_ui_setting()

    def init_image_page(self):
        self.img_queue = deque()
        self.current_image_index = -1
        imgs_list = glob.glob(IMG_PATH + "/*.jpg")
        imgs_list.sort(key=lambda f: os.path.getctime(f))
        self.img_queue.clear()
        self.img_queue.extend(imgs_list)
        self.show_image(self.current_image_index)
        self.radar_viewer.pushButton_pre.clicked.connect(self.pre_image)
        self.radar_viewer.pushButton_next.clicked.connect(self.next_image)

    def init_threads(self):
        self.camera_image_queue = deque(maxlen=6)
        self.detector_output_queue = deque(maxlen=3)
        self.detector_thread = DetectorThread(self,  self.camera_image_queue, self.detector_output_queue, False)
        self.detector_thread.start()

        self.radar_viewer.detector_thread.yolo_initial_finished.connect(self.set_detector_enable)

        self.camera_thread = CameraThread(self, self.cam_manager.cam, self.camera_image_queue)
        self.camera_thread.start()

        self.com = None
        self.radar_receive_thread = None

    def init_timers(self):
        self.frame_update_timer = QTimer(self)
        self.frame_update_timer.timeout.connect(self.display_image)
        self.frame_update_timer.start(6)

        self.radar_update_timer = QTimer(self)
        self.radar_update_timer.timeout.connect(self.update_radar_from_obj_queue)
        #self.radar_update_timer.start(30)

    def start_camera_setting_dialog(self):
        self.camera_setting_dialog = camera_setting.CameraSettingDialog(self.cam_manager)
        self.camera_setting_dialog.camera_setting_signal.connect(self.update_camera_info)
        self.camera_setting_dialog.show()

    def start_serial_setting_dialog(self):
        try:
            if self.com:
                if self.radar_receive_thread:
                    self.radar_receive_thread.exit()
                self.com.close()

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

        self.frame_update_timer.start()

        self.camera_thread.set_cam(self.radar_viewer.cam_manager.cam)
        self.camera_thread.start()

    def update_uart_info(self, uart_config_msg):
        #self.radar_update_timer.stop()
        self.uart_cfg = uart_config_msg
        self.com = UartManager.create_instance(self.uart_cfg)

        self.radar_receive_thread = radar.RadarReceiveThread(self, self.com)
        self.radar_msg_process_thread = radar.RadarMsgProcessThread(self)

        self.radar_receive_thread.start()
        self.radar_msg_process_thread.start()


        #self.radar_update_timer.start(60)



    def set_video_brightness(self):
        self.cam_manager.brightness = self.radar_viewer.horizontalSlider_video_brightness.value()
        self.cam_manager.cam.set_brightness(self.cam_manager.brightness)

    def set_video_contrast(self):
        self.cam_manager.contrast = self.radar_viewer.horizontalSlider_video_contrast.value()
        self.cam_manager.cam.set_contrast(self.cam_manager.contrast)

    def set_detector_enable(self, *args):
        detector_finished_flag = args[0]
        if detector_finished_flag == True:
            self.radar_viewer.checkBox_detector_switch.setEnabled(True)
        else:
            self.radar_viewer.checkBox_detector_switch.setEnabled(False)


    def clear_scatter(self):
        if self.scatter_collection:
            self.scatter_collection.remove()
            self.qtfig.fig.canvas.draw_idle()
            del self.scatter_collection
            self.scatter_collection = None

    def plot_scatter(self, x, y):
        # [text.remove() for text in reversed(self.qtfig.axes.texts)]
        try:
            self.clear_scatter()

            self.scatter_collection = self.qtfig.axes.scatter(x, y, c='red')
        except Exception as e:
            print("scatter err")
            print(e)

        # for x1, y1 in zip(x, y):
        #     self.qtfig.axes.text(x1, y1, '({},{})'.format(round(x1, 1), round(y1, 1)))

    # def update_radar(self, *args):
    #     #print(args)
    #     x, y, x_size, y_size = args[0]
    #     #plt.clf()
    #     self.plot_scatter(x, y)
    #
    #     for x1, y1 in zip(x, y):
    #         if self.radar_startx <= x1 <= self.radar_startx + self.radar_capture_width \
    #                 and self.radar_starty <= y1 <= self.radar_starty + self.radar_capture_deepth:
    #             self.obstacle_in_area = True
    #             return

    def update_radar_from_obj_queue(self):
        radar_update_start_time = time.time()
        # print('radar update time:',radar_update_start_time)
        try:
            print("radar obj msg queue:", len(radar.radar_obj_msg_queue))
            if len(radar.radar_obj_msg_queue) == 0:
                self.clear_scatter()
                return

            x, y, x_size, y_size = radar.radar_obj_msg_queue.popleft()
            self.plot_scatter(x, y)

            for x1, y1 in zip(x, y):
                if self.radar_startx <= x1 <= self.radar_startx + self.radar_capture_width \
                        and self.radar_starty <= y1 <= self.radar_starty + self.radar_capture_deepth:
                    self.obstacle_in_area = True
                    return

        except IndexError as e:
            print('queue is empty')
            self.clear_scatter()
            print(e)
        except Exception as e:
            print('other err')
            print(e)

        finally:
            print('radar update cost time:', time.time() - radar_update_start_time)

    def display_image(self):
        start_time = time.time()
        self.update_radar_from_obj_queue()
        try:
            start_time = time.time()
            frame = None
            if self.detector_enable:
                print('detector output queue len:',len(self.detector_output_queue))
                if len(self.detector_output_queue) > 0:
                    frame = self.detector_output_queue.popleft()
                else:
                    return
            else:
                print('camera image queue len:',len(self.camera_image_queue))
                if len(self.camera_image_queue) > 0:
                    frame = self.camera_image_queue.popleft()
                else:
                    return

            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.radar_viewer.label_video.setPixmap(pixmap)
            print("display time cost:",time.time() - start_time)
        except Exception as e:
            print(e)

        print('display cost time:', time.time() - start_time)
        # ret, frame = self.cam_manager.cam.take_photo()
        # if ret == True:
        #     # gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        #         #     # 找到棋盘格角点
        #     # ret, corners = cv.findChessboardCorners(gray, (CHESSBOARD_W_NUM, CHESSBOARD_H_NUM), None)
        #     # if ret == True:
        #     #     cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), CRITERIA)
        #     #     cv.drawChessboardCorners(frame, (w, h), corners, ret)
        #
        #     #imagePoints = cv.projectPoints(objectPoints, rvec, tvec, mtx, dist)
        #
        #     self.exist_person = False
        #     if self.detector_enable:
        #         detector_input_queue.append(frame)
        #         frame = detector_input_queue.popleft()
        #         # start = time.time()
        #         # frame1 = Image.fromarray(frame)
        #         # _, self.exist_person = self.detector.detect_image(frame1)
        #         # frame = np.asarray(frame1)
        #         # stop = time.time()
        #         # print("detector processing time:",stop - start)
        #         # self.frame_update_timer.stop()
        #
        #     display_queue.append(frame)
        #
        #     #point = np.array(imagePoints[0][0, 0, :]).astype(int)
        #     #cv.circle(frame, tuple(point), 2, (0, 0, 255), 4)
        #
        #     #cv.rectangle(frame, tuple(point - 20), tuple(point + 20), (0, 255, 0), 3)
        #     #cv.putText(frame, "({},{}),1.2m/s".format(objectPoints[0, 0] / 1000, objectPoints[0, 2] / 1000),
        #     #           (point[0] - 20, point[1] - 25), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        #
        #     # self.frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        #     # # print(type(self.frame))
        #     # stored_flag = False
        #     # if self.cv_trigger_enable:
        #     #     if self.exist_person:
        #     #         self.save_img(self.frame)
        #     #         stored_flag = True
        #     #
        #     # if self.radar_trigger_enable and not stored_flag:
        #     #     if self.obstacle_in_area:
        #     #         self.obstacle_in_area = False
        #     #         self.save_img(self.frame)
        #     #
        #     # self.image = QImage(self.frame.data, self.frame.shape[1], self.frame.shape[0], QImage.Format_RGB888)
        #     # self.pixmap = QPixmap.fromImage(self.image)
        #     # # self.scaled_pixmap = self.pixmap.scaled(
        #     # #     self.video_width, self.video_height, aspectRatioMode=Qt.KeepAspectRatioByExpanding,
        #     # #     transformMode=Qt.SmoothTransformation)
        #     # self.radar_viewer.label_video.setPixmap(self.pixmap)

    # def set_save_picture_auto(self):
    #     if self.radar_viewer.checkBox_save_picture_auto.checkState() == Qt.Checked:
    #         self.save_picture_auto = True
    #     elif self.radar_viewer.checkBox_save_picture_auto.checkState() == Qt.Unchecked:
    #         self.save_picture_auto = False

    # def resizeEvent(self, event):
    #     # print("resize event")
    #     pass
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

    def save_img(self, img):
        filename = time.ctime().replace(":", " ")
        img_name = "{}\\{}.jpg".format(os.path.realpath(IMG_PATH), filename)
        if cv.imwrite(img_name, img):
            self.img_queue.append(img_name)
            self.show_image(self.current_image_index)

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = Radar_Viewer()
    main_window.show()
    sys.exit(app.exec_())
