from camera import CameraManager

class A():
    def __init__(self):
        device_list = CameraManager().list_cameras()
        index = 0

        for name in device_list:
            print(str(index) + ': ' + name)
            index += 1

a = A()
