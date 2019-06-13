import serial
import serial.tools.list_ports as list_ports
from threading import Thread
from queue import Queue

PARITY_DICT = {
    "None" : serial.PARITY_NONE,
    "Even" : serial.PARITY_EVEN,
    "Odd" : serial.PARITY_ODD,
    "Mark" : serial.PARITY_MARK,
    "Space" : serial.PARITY_SPACE,
}

STOPBITS_DICT = {
    "1-bit" : serial.STOPBITS_ONE,
    "1.5-bit" : serial.STOPBITS_ONE_POINT_FIVE,
    "2-bit" : serial.STOPBITS_TWO,
}

BYTESIZE_DICT = {
    "5-bit" : serial.FIVEBITS,
    "6-bit" : serial.SIXBITS,
    "7-bit" : serial.SEVENBITS,
    "8-bit" : serial.EIGHTBITS,
}

BAUDRATES = (9600, 19200, 38400, 57600, 115200, 230400, 460800, 500000,
                 576000, 921600, 1000000, 1152000, 1500000, 2000000, 2500000,
                 3000000, 3500000, 4000000)


class UartConfig():
    def __init__(self, com_id = "COM0", baudrate = 115200, timeout = None, bytesize = serial.EIGHTBITS,
                 stopbits = serial.STOPBITS_ONE, parity = serial.PARITY_NONE):
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
        self.com = serial.Serial(config.com_id.upper(), baudrate = config.baudrate,
                                 bytesize = config.bytesize, stopbits = config.stopbits,
                                 parity =   config.parity, timeout=config.timeout)
        if not self.com.is_open:
            self.com.open()

        return self.com



class UartReceiveThread():
    def __init__(self, com, msg_queue):
        self.com = com
        self.msg_queue = msg_queue
        self.count = 0

    def run(self):
        self.read_buff = []
        while self.com.is_open:

            lines = self.com.readlines()
            if not lines:
                self.read_buff.extend(lines)
                self.valid_datas = self.check_valid_package()
                for valid_data in self.valid_datas:
                    self.msg_queue.put(valid_data)



    def check_valid_package(self):
        self.count += 1
        return [self.count]

def print_msg(msg_queue):
    while True:
        if msg_queue.qsize():
            print(msg_queue.get())


if __name__ == '__main__':
    com_name = UartManager.list_ports()[0]
    cfg = UartConfig(com_name, timeout=1)
    com = UartManager.create_instance(cfg)
    msg_queue = Queue()
    uart_receiver = UartReceiveThread(com,msg_queue)

    receiver_thread = Thread(target=uart_receiver.run)
    receiver_thread.start()

    print_thread = Thread(target = print_msg, args=(msg_queue,))
    print_thread.start()
    receiver_thread.join()
    print_thread.join()

#__all__ = ["PARITY_DICT”, BYTESIZE_DICT, BAUDRATES, STOPBITS_DICT, UartConfig, UartManager, UartReceiveThread]