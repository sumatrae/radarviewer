import time
import numpy as np
from .yolo import YOLO
from PyQt5.QtCore import QThread, pyqtSignal
from PIL import Image


class DetectorThread(QThread):
    def __init__(self, parent, input_queue, output_queue, enable):
        super(DetectorThread, self).__init__(parent)

        self.input_queue = input_queue
        self.output_queue = output_queue
        self.enable = enable

    def __del__(self):
        del self.detector

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

            while True:
                if not self.enable:
                    continue

                print('camera image queue len:', len(self.input_queue))
                if len(self.input_queue) > 0:

                    frame = self.input_queue.popleft()

                    frame1 = Image.fromarray(frame)
                    _, exist_person = self.detector.detect_image(frame1)
                    frame = np.asarray(frame1)

                    self.output_queue.append(frame)
                else:
                    time.sleep(0.01)

        except Exception as e:
            print(e)
