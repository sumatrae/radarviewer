from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi

from camera import CameraCfg

class CameraSettingDialog(QDialog):
    camera_setting_signal = pyqtSignal(CameraCfg)

    def __init__(self, camera_config, *args):
        super(CameraSettingDialog, self).__init__(*args)
        self.init_ui(camera_config)

        self.camera_setting_dialog.buttonBox.clicked.connect(self.send_edited_camera_cfg)

    def init_ui(self, camera_config):
        self.camera_setting_dialog = loadUi("./ui/camera_setting.ui", self)
        self.camera_setting_dialog.comboBox_camera.addItems(camera_config.camera_list)
        self.camera_setting_dialog.comboBox_camera.setCurrentIndex(camera_config.id)
        self.camera_setting_dialog.lineEdit_framerate.setText(str(camera_config.framerate))
        self.camera_setting_dialog.lineEdit_width.setText(str(camera_config.resolution[0]))
        self.camera_setting_dialog.lineEdit_height.setText(str(camera_config.resolution[1]))
        self.camera_setting_dialog.lineEdit_brightness.setText(str(camera_config.brightness))
        self.camera_setting_dialog.lineEdit_contrast.setText(str(camera_config.contrast))
        self.camera_setting_dialog.lineEdit_gain.setText(str(camera_config.gain))

    def send_edited_camera_cfg(self):
        self.camera_cfg = CameraCfg()
        self.camera_cfg.id = self.camera_setting_dialog.comboBox_camera.currentIndex()
        self.camera_cfg.framerate = float(self.camera_setting_dialog.lineEdit_framerate.text())
        self.camera_cfg.resolution[0] = float(self.camera_setting_dialog.lineEdit_width.text())
        self.camera_cfg.resolution[1] = float(self.camera_setting_dialog.lineEdit_height.text())
        self.camera_cfg.brightness = float(self.camera_setting_dialog.lineEdit_brightness.text())
        self.camera_cfg.contrast = float(self.camera_setting_dialog.lineEdit_contrast.text())
        self.camera_cfg.gain = float(self.camera_setting_dialog.lineEdit_gain.text())

        self.camera_setting_signal.emit(self.camera_cfg)
