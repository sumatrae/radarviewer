from collections import deque

import serial
import serial.tools.list_ports as list_ports
from queue import Queue
import time
import struct
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

PARITY_DICT = {
    "None": serial.PARITY_NONE,
    "Even": serial.PARITY_EVEN,
    "Odd": serial.PARITY_ODD,
    "Mark": serial.PARITY_MARK,
    "Space": serial.PARITY_SPACE,
}

STOPBITS_DICT = {
    "1-bit": serial.STOPBITS_ONE,
    "1.5-bit": serial.STOPBITS_ONE_POINT_FIVE,
    "2-bit": serial.STOPBITS_TWO,
}

BYTESIZE_DICT = {
    "5-bit": serial.FIVEBITS,
    "6-bit": serial.SIXBITS,
    "7-bit": serial.SEVENBITS,
    "8-bit": serial.EIGHTBITS,
}

BAUDRATES = (9600, 19200, 38400, 57600, 115200, 230400, 460800, 500000,
             576000, 921600, 1000000, 1152000, 1500000, 2000000, 2500000,
             3000000, 3500000, 4000000)

HEADER_SIZE = 40
MAX_NUM_OBJECTS = 200
OBJ_STRUCT_SIZE_BYTES = 8
MAX_NUM_CLUSTERS = 24
CLUSTER_STRUCT_SIZE_BYTES = 8
MAX_NUM_TRACKERS = 24
TRACKER_STRUCT_SIZE_BYTES = 12
STATS_SIZE_BYTES = 16

MMWDEMO_UART_MSG_DETECTED_POINTS = 1
MMWDEMO_UART_MSG_CLUSTERS = 2
MMWDEMO_UART_MSG_TRACKED_OBJ = 3
MMWDEMO_UART_MSG_PARKING_ASSIST = 4
MMWDEMO_UART_MSG_STATS = 6

TLV_HEADER_LEN = 8
OBJ_DESC_LEN = 4

radar_raw_msg_queue = deque(maxlen=10)


class UartConfig():
    def __init__(self, com_id="COM0", baudrate=921600, timeout= None, bytesize=serial.EIGHTBITS,
                 stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE):
        self.com_id = com_id
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.stopbits = stopbits
        self.parity = parity
        self.timeout = timeout


class UartManager():
    @classmethod
    def list_ports(self):
        ports_obj = list_ports.comports()

        ports_list = []
        for port_obj in ports_obj:
            ports_list.append(port_obj.device)

        return ports_list

    @classmethod
    def create_instance(self, config):
        self.com = serial.Serial(config.com_id.upper(), baudrate=config.baudrate,
                                 bytesize=config.bytesize, stopbits=config.stopbits,
                                 parity=config.parity, timeout=config.timeout)
        if not self.com.is_open:
            self.com.open()

        return self.com


class RadarReceiveThread(QThread):
    update = pyqtSignal(tuple)

    def __init__(self, parent, com):
        super(RadarReceiveThread, self).__init__(parent)
        self.com = com

    def run(self):
        self.com.reset_input_buffer()
        self.read_buffer = bytes()
        while self.com.is_open:
            try:
                lines = self.com.read(4096)
                if lines:
                    self.read_buffer += lines
                    self.find_radar_frame()
            except Exception as e:
                self.read_buffer = bytes()
                #print('radar uart receive thread err')
                #print(e)

    def find_radar_frame(self):
        buffer_len = len(self.read_buffer)

        print("buffer length:", buffer_len)

        while buffer_len >= HEADER_SIZE:

            hex_str = self.read_buffer.hex()
            index = hex_str.find("0201040306050807")

            if index == -1:
                return

            elif index > 0:
                self.read_buffer = self.read_buffer[index // 2:]

                buffer_len = len(self.read_buffer)
                if HEADER_SIZE > buffer_len:
                    return

            header = self.read_buffer[:HEADER_SIZE]
            magic_word, version, total_package_length, platform, frame_number, time_cpucycle, num_detected_objection, \
            num_tlvs, sumframe_numbers = [i for i in struct.unpack("<QIIIIIIII", header)]

            if 0x0a1642 != platform:
                self.read_buffer = self.read_buffer[HEADER_SIZE:]
                return

            if buffer_len >= total_package_length:

                main_payload = self.read_buffer[HEADER_SIZE:total_package_length]
                radar_raw_msg_queue.append((num_tlvs, main_payload))

                if total_package_length % 32 != 0:
                    total_package_length = 32 * ((total_package_length // 32) + 1)

                self.read_buffer = self.read_buffer[total_package_length:]


class RadarMsgProcessThread(QThread):
    update = pyqtSignal(tuple)

    def __init__(self, parent):
        super(RadarMsgProcessThread, self).__init__(parent)

    def run(self):
        while True:
            try:
                tlvs_num, payload = radar_raw_msg_queue.popleft()
                # print(tlvs_num)
                # print(payload)
                self.parser_main_payload(tlvs_num, payload)
            except IndexError as e:
                #print(e)
                time.sleep(0.06)

    def parser_main_payload(self, num_tlvs, main_payload):
        try:
            if num_tlvs > MAX_NUM_TRACKERS:
                return

            if main_payload is None:
                return

            for i in range(num_tlvs):
                tlv_header = main_payload[:TLV_HEADER_LEN]
                if len(tlv_header) != TLV_HEADER_LEN:
                    print("tlv header len err:", len(tlv_header))
                    continue

                tlv_type, tlv_length = struct.unpack("<II", tlv_header)
                tlv_payload = main_payload[TLV_HEADER_LEN:TLV_HEADER_LEN + tlv_length]

                if tlv_type == MMWDEMO_UART_MSG_CLUSTERS:
                    pass
                    # print("MMWDEMO_UART_MSG_CLUSTERS")
                    # x, y, x_size, y_size = self.get_clusters_loction(tlv_payload)
                    # msg_queue.put((x, y, x_size, y_size))
                    # print((x, y, x_size, y_size))
                    # self.update.emit((x, y, x_size, y_size))
                elif tlv_type == MMWDEMO_UART_MSG_TRACKED_OBJ:
                    x, y, dx, dy = self.get_trackers(tlv_payload)
                    # msg_queue.put((x, y, x_size, y_size))
                    # print((x, y, x_size, y_size))
                    self.update.emit((x, y, dx, dy))

                else:
                    # print("other msg")
                    pass

                main_payload = main_payload[TLV_HEADER_LEN + tlv_length:]
        except Exception as e:
            print('radar msg processing thread err')
            print(e)

    def get_clusters_loction(self, tlv_payload):
        obj_description = tlv_payload[:OBJ_DESC_LEN]
        obj_payload = tlv_payload[OBJ_DESC_LEN:]
        obj_num, xyz_qformat = struct.unpack("<HH", obj_description)

        xyx_qformat = pow(1 / 2, xyz_qformat)

        x = np.zeros(obj_num)
        y = np.zeros(obj_num)
        x_size = np.zeros(obj_num)
        y_size = np.zeros(obj_num)

        for j in range(obj_num):
            obj = obj_payload[j * CLUSTER_STRUCT_SIZE_BYTES:(j + 1) * CLUSTER_STRUCT_SIZE_BYTES]
            x[j], y[j], x_size[j], y_size[j] = [s for s in struct.unpack("<HHHH", obj)]

        x[x > 32767] = x[x > 32767] - 65535
        y[y > 32767] = y[y > 32767] - 65535
        x *= xyx_qformat
        y *= xyx_qformat
        x_size *= xyx_qformat
        y_size *= xyx_qformat

        area = 4 * x_size * y_size
        x_size[x_size > 20] = np.inf

        return x, y, x_size, y_size

    def get_trackers(self, tlv_payload):
        obj_description = tlv_payload[:OBJ_DESC_LEN]
        obj_payload = tlv_payload[OBJ_DESC_LEN:]
        obj_num, xyz_qformat = struct.unpack("<HH", obj_description)

        xyx_qformat = pow(1 / 2, xyz_qformat)

        x = np.zeros(obj_num)
        y = np.zeros(obj_num)
        dx = np.zeros(obj_num)
        dy = np.zeros(obj_num)
        x_size = np.zeros(obj_num)
        y_size = np.zeros(obj_num)

        for j in range(obj_num):
            obj = obj_payload[j * TRACKER_STRUCT_SIZE_BYTES:(j + 1) * TRACKER_STRUCT_SIZE_BYTES]
            x[j], y[j], dx[j], dy[j], x_size[j], y_size[j] = [s for s in struct.unpack("<HHHHHH", obj)]

        x[x > 32767] = x[x > 32767] - 65535
        y[y > 32767] = y[y > 32767] - 65535
        dx[dx > 32767] = dx[dx > 32767] - 65535
        dy[dy > 32767] = dy[dy > 32767] - 65535
        x *= xyx_qformat
        y *= xyx_qformat
        dx *= xyx_qformat
        dy *= xyx_qformat
        x_size *= xyx_qformat
        y_size *= xyx_qformat

        return x, y, dx, dy
