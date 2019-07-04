from PyQt5.QtCore import QThread, pyqtSignal


class DetectorThread(QThread):

    def __init__(self, parent):
        super(DetectorThread, self).__init__(parent)

    def run(self):
        pass
