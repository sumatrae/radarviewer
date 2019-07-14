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

        self.count = 0

    def __del__(self):
        print("CameraThread exit")

    def set_cam(self, cam):
            self.cam = cam

    def run(self):
        try:
            while self.cam.is_opened():
                try:
                    ret, frame = self.cam.take_photo()
                    if ret == True:
                        # self.count += 1
                        # if self.count % 2 == 0:
                        #     continue

                        self.camera_image_queue.append(frame)
                    else:
                        time.sleep(1.0/self.frame)
                except Exception as e:
                    print('take photo err')
                    print(e)
            print("CameraThread normal exit")
        except Exception as e:
            print('CameraThread exit')
            print(e)
