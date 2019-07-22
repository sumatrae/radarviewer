import camera
from . import camera_list
print(camera_list.camera_list)
class CameraCfg():
    def __init__(self):
        self.camera_list = []
        self.id = 0
        self.framerate = 30
        self.resolution = [1280,720]
        self.brightness = 50
        self.contrast = 20
        self.gain = 0
        self.cam = None

class CameraManager(CameraCfg):
    def __init__(self):
        super(CameraManager, self).__init__()
        self.init_camera_info()

    def init_camera_info(self,):
        self.id = 0
        self.camera_list = camera_list.camera_list

        self.cam = self.get_camera_instance(self.id)
        if self.cam:
            self.set_camera_cfg()
            self.read_camera_cfg()

    def update_camera_info(self, id):
        self.cam = self.get_camera_instance(id)
        if self.cam:
            self.set_camera_cfg()
            self.read_camera_cfg()


    def read_camera_cfg(self):
        self.framerate = self.cam.get_framerate()
        self.resolution = self.cam.get_resolution()
        self.brightness = self.cam.get_brightness()
        self.contrast = self.cam.get_contrast()
        self.gain = self.cam.get_gain()

    def set_camera_cfg(self):
        self.cam.set_framerate(self.framerate)
        self.cam.set_resolution(self.resolution[0],self.resolution[1])
        self.cam.set_brightness(self.brightness)
        self.cam.set_contrast(self.contrast)
        self.cam.set_gain(self.gain)

    def get_camera_instance(self,id):
        if isinstance(self.cam, camera.Camera):
            self.cam.close()
            #return self.cam

        self.id = id
        self.cam = camera.Camera(id)
        return self.cam