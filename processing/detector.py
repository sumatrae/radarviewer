import time
import numpy as np

from PyQt5.QtCore import (QThread, pyqtSignal,QObject)
from PIL import Image
import cv2 as cv
from PyQt5.QtGui import (QImage, QIntValidator, QPixmap, QRegExpValidator)

from multiprocessing import Process

class DetectorThread(QThread):
    save_img_flag = False
    yolo_initial_finished = pyqtSignal(bool)
    def __init__(self, parent, input_queue, output_queue, label, enable):
        super(DetectorThread, self).__init__(parent)

        print("DetectorThread started")

        self.input_queue = input_queue
        self.output_queue = output_queue
        self.label = label
        self.enable = enable

    # def __del__(self):
    #     #self.yolo_initial_finished.emit(False)
    #     del self.detector

        #print('DetectorThread exit')

    def _try_dectecor_session(self):
        '''第一次调用yolo时很慢，防止界面卡顿，在启动时先调用一次'''
        frame = np.zeros((32, 32, 3)).astype('uint8')
        frame1 = Image.fromarray(frame)
        _, _ = self.detector.detect_image(frame1)

    def set_enable(self, enable):
        self.enable = enable

    def run(self):
        try:
            if self.enable:
                from .yolo import YOLO
                self.detector = YOLO()
                self._try_dectecor_session()
                self.yolo_initial_finished.emit(True)
                print('Yolo init finished')

            while True:

                start_time = time.time()
                #print('camera image queue len:', len(self.input_queue))
                if len(self.input_queue) > 0:

                    frame = self.input_queue.popleft()

                    if  self.enable:
                        frame1 = Image.fromarray(frame)
                        _, exist_person = self.detector.detect_image(frame1)
                        frame = np.asarray(frame1)
                        end_time_1 = time.time()
                        print('detector time cost:', end_time_1 - start_time)
                    else:
                        end_time_1 = time.time()
                    frame = cv.resize(frame,(1280,720))
                    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                    image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(image)
                    self.label.setPixmap(pixmap)


                    # print('display time cost:', time.time() - end_time_1)

                    #self.output_queue.append(pixmap)
                else:
                    time.sleep(0.03)
                    #self.msleep(30)

        except Exception as e:
            print(e)

    def save_img(self, *args):
        self.save_img_flag = True


class DetectorProcess(Process):
    #yolo_initial_finished = pyqtSignal(bool)
    def __init__(self,input_queue, output_queue, enable):
        super(DetectorProcess, self).__init__()
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.enable = enable

    def _try_dectecor_session(self):
        '''第一次调用yolo时很慢，防止界面卡顿，在启动时先调用一次'''
        frame = np.zeros((32, 32, 3)).astype('uint8')
        frame1 = Image.fromarray(frame)
        _, _ = self.detector.detect_image(frame1)

    def set_enable(self, enable):
        self.enable = enable

    def run(self):
        try:
            self.detector = YOLO()
            self._try_dectecor_session()
            #self.yolo_initial_finished.emit(True)
            print('Yolo init finished')

            while True:
                if not self.enable:
                    continue

                print('camera image queue len:', len(self.input_queue))
                if len(self.input_queue) > 0:

                    frame = self.input_queue.popleft()

                    frame1 = Image.fromarray(frame)
                    _, exist_person = self.detector.detect_image(frame1)
                    frame = np.asarray(frame1)

                    #frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                    image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(image)

                    self.output_queue.append(pixmap)
                else:
                    time.sleep(0.01)

        except Exception as e:
            print(e)