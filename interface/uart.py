import serial

class Uart():
    def __init__(self, com_id, baudrate, timeout):
        self.com_id = com_id
        self.baudrate = baudrate
        self.timeout = timeout

    def open(self):
        self.com = serial.Serial(self.com_id.upper(), self.baudrate, timeout = self.timeout)
        if not self.com.is_open:
            self.com.open()


    def close(self):
        if self.com.is_open:
            self.com.close()

    def list_coms(self):
        pass

    def set_port(self, port):
        self.port = port

    def get_port(self):
        return self.port

    def set_baudrate(self, baudrate):
        self.baudrate = baudrate

    def get_baudrate(self):
        return self.baudrate

    def read(self):
        pass

    def write(self):
        pass