from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi


class AboutDialog(QDialog):
    def __init__(self, *args):
        super(AboutDialog, self).__init__(*args)
        self.serial_setting_dialog = loadUi("./ui/about.ui", self)
        self.serial_setting_dialog.label.setText(str("<font>成都多普勒科技有限公司 Copyright&copy;2019</font>"))
