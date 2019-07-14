import time
from PyQt5.QtCore import QThread

class CameraThread(QThread):
    def __init__(self, parent, cam, camera_image_queue):
        super(CameraThread, self).__init__(parent)
        self.cam = cam
        self.camera_image_queue = camera_image_queue
        if self.cam != None:
            self.frame = self.cam.get_framerate()
        else:
            self.frame = 30

    def __del__(self):
        self.cam.close()

    def set_com(self, cam):
        self.cam = cam

    def run(self):
        while True:
            try:
                if  self.cam == None:
                    continue

                ret, frame = self.cam.take_photo()
                if ret == True:
                    self.camera_image_queue.append(frame)
                else:
                    time.sleep(1.0/self.frame)
            except Exception as e:
                print(e)
