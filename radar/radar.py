from collections import deque


class Obstacle():
    def __init__(self,x,y,v):
        self.x = x
        self.y = y
        self.v = v


class ObstacleList():
    def __init__(self):
        self.all_obstacle = deque()




class Radar():
    def __init__(self):
        pass

    def open(self):
        pass

    def read(self):
        pass

    def write(self):
        pass

    def get_location(self):
        pass

    def get_velocity(self):
        pass

    def get_signal_power(self):
        pass
