import cv2 as cv
import time

class Camera():
    count = 0
    def __init__(self,camera_id):
        self.camera_id = camera_id
        self.cap_fd = self.open()
        if self.is_opened():
            self.framerate =  self.get_framerate()
            self.interval = (int)(1000.0/self.framerate)

    def open(self):
        self.cap_fd = cv.VideoCapture(self.camera_id)
        if not self.cap_fd.isOpened():
            print("Open camera({}) failed".format(self.camera_id))
        self.cap_fd.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        return self.cap_fd

    def is_opened(self):
        return self.cap_fd.isOpened()

    def close(self):
        self.cap_fd.release()

    def set_framerate(self, frame_rate):
        self.cap_fd.set(cv.CAP_PROP_FPS, int(frame_rate))

    def get_framerate(self):
        return self.cap_fd.get(cv.CAP_PROP_FPS)

    def set_resolution(self,width,hight):
        self.cap_fd.set(cv.CAP_PROP_FRAME_WIDTH, int(width))
        self.cap_fd.set(cv.CAP_PROP_FRAME_HEIGHT, int(hight))

    def get_resolution(self):
        width = self.cap_fd.get(cv.CAP_PROP_FRAME_WIDTH)
        height = self.cap_fd.get(cv.CAP_PROP_FRAME_HEIGHT)
        return [width, height]

    def set_brightness(self, brightness):
        self.cap_fd.set(cv.CAP_PROP_BRIGHTNESS, brightness)

    def get_brightness(self):
        return self.cap_fd.get(cv.CAP_PROP_BRIGHTNESS)

    def set_contrast(self, contrast):
        self.cap_fd.set(cv.CAP_PROP_CONTRAST, contrast)

    def get_contrast(self):
        return self.cap_fd.get(cv.CAP_PROP_CONTRAST)

    def set_saturation (self, saturation):
        self.cap_fd.set(cv.CAP_PROP_SATURATION, saturation)

    def get_saturation(self):
        return self.cap_fd.get(cv.CAP_PROP_SATURATION)

    def set_hue(self, hue):
        self.cap_fd.set(cv.CAP_PROP_HUE, hue)

    def get_hue(self):
        return self.cap_fd.get(cv.CAP_PROP_HUE)

    def set_gain(self, gain):
        self.cap_fd.set(cv.CAP_PROP_GAIN, gain)

    def get_gain(self):
        return self.cap_fd.get(cv.CAP_PROP_GAIN)

    def set_exposure(self, exposure):
        self.cap_fd.set(cv.CAP_PROP_EXPOSURE, exposure)

    def get_exposure(self):
        return self.cap_fd.get(cv.CAP_PROP_EXPOSURE)

    def start_recording(self):
        pass

    def stop_recording(self):
        pass

    def take_photo(self):
        #start_time = time.time()
        ret, frame = self.cap_fd.read()
        self.count += 1
        print(self.count)
        #print('get frame cost:',time.time() - start_time)
        #cv.waitKey(1)
        return ret,frame

    def annoate(self):
        pass



if __name__ == '__main__':

    cam = Camera(0)
    cam.set_framerate(120)
    cam.set_resolution(1280,720)

    print(cam.get_framerate())
    print(cam.get_resolution())

    cam.set_brightness(128)
    print(cam.get_brightness())
    print(cam.get_contrast())

    #cam.set_exposure(0)
    print(cam.get_exposure())

    while 1:
        _,photo = cam.take_photo()
        cv.imshow("photo", photo)



