import camera
from . import camera_list
print(camera_list.camera_list)
class CameraCfg():
    def __init__(self):
        self.camera_list = []
        self.id = 0
        self.framerate = 30
        self.resolution = (1280,720)
        self.brightness = 0
        self.contrast = 0
        self.gain = 0
        self.cam = None

class CameraManager(CameraCfg):
    def __init__(self):
        super(CameraManager, self).__init__()
        self.init_camera_info()

    def read_camera_cfg(self):
        self.framerate = self.cam.get_framerate()
        self.resolution = self.cam.get_resolution()
        self.brightness = self.cam.get_brightness()
        self.contrast = self.cam.get_contrast()
        self.gain = self.cam.get_gain()

    def init_camera_info(self,):
        self.id = 0
        self.camera_list = camera_list.camera_list

        self.cam = self.get_camera_instance()
        if self.cam:
            self.read_camera_cfg()


    def update_camera_info(self, id):
        if self.id == id:
            return

        self.id = id
        self.cam = self.get_camera_instance()
        if self.cam:
            self.read_camera_cfg()


    def get_camera_instance(self):
        if isinstance(self.cam, camera.Camera):
            return self.cam

        self.cam = camera.Camera(self.id)
        return self.cam