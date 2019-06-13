import configparser
import gc
import os
import re
import sys

from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread
from PyQt5.QtGui import QIcon, QPalette, QImage,QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox
from PyQt5.uic import loadUi

from radar import *
from PyQt5.QtCore import pyqtSignal
import cv2

parity_invers = dict(zip(PARITY_DICT.values(), PARITY_DICT.keys()))
bytesize_invers = dict(zip(BYTESIZE_DICT.values(), BYTESIZE_DICT.keys()))
stopbits_invers = dict(zip(STOPBITS_DICT.values(), STOPBITS_DICT.keys()))

class SerialSettingDialog(QDialog):
    serial_setting_signal = pyqtSignal(UartConfig)
    def __init__(self, uart_setting, *args):
        super(SerialSettingDialog, self).__init__(*args)
        self.init_ui(uart_setting)

        self.serial_setting_dialog.buttonBox.accepted.connect(self.send_edited_uart_cfg)

    def init_ui(self, uart_setting):
        self.serial_setting_dialog = loadUi("./ui/serial_setting.ui", self)
        self.serial_setting_dialog.comboBox_port.addItems(UartManager.list_ports())
        self.serial_setting_dialog.comboBox_port.setCurrentText(uart_setting.com_id)

        self.serial_setting_dialog.comboBox_baudrate.addItems([str(i) for i in BAUDRATES])
        self.serial_setting_dialog.comboBox_baudrate.setCurrentText(str(uart_setting.baudrate))

        self.serial_setting_dialog.comboBox_parity.addItems(PARITY_DICT.keys())
        self.serial_setting_dialog.comboBox_parity.setCurrentText(parity_invers[uart_setting.parity])

        self.serial_setting_dialog.comboBox_datawidth.addItems(BYTESIZE_DICT.keys())
        self.serial_setting_dialog.comboBox_datawidth.setCurrentText(bytesize_invers[uart_setting.bytesize])

        self.serial_setting_dialog.comboBox_stopbit.addItems(STOPBITS_DICT.keys())
        self.serial_setting_dialog.comboBox_stopbit.setCurrentText(stopbits_invers[uart_setting.stopbits])

    def send_edited_uart_cfg(self):
        self.uart_cfg = UartConfig()
        self.uart_cfg.com_id = self.serial_setting_dialog.comboBox_port.currentText()
        self.uart_cfg.baudrate = int(self.serial_setting_dialog.comboBox_baudrate.currentText())
        self.uart_cfg.parity = PARITY_DICT[self.serial_setting_dialog.comboBox_parity.currentText()]
        self.uart_cfg.bytesize = BYTESIZE_DICT[self.serial_setting_dialog.comboBox_datawidth.currentText()]
        self.uart_cfg.stopbits = STOPBITS_DICT[self.serial_setting_dialog.comboBox_stopbit.currentText()]

        self.serial_setting_signal.emit(self.uart_cfg)
