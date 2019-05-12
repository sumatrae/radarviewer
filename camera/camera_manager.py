import camera
#import device


class CameraManager():
    def __init__(self):
        self.default_id = 0
        self.set_camera_id(self.default_id)

    def list_cameras(self):
        import device
        device_list = []
        try:
            device_list = device.getDeviceList()
        except Exception as e:
            print(e)

        return device_list

    def set_camera_id(self, camera_id):
        self.camera_id = camera_id

    def get_camera_id(self):
        return self.camera_id

    def get_camera_instance(self):
        print(self.camera_id)
        return camera.Camera(self.camera_id)