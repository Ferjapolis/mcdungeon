from utils import Vec


class Door(object):

    def __init__(self):
        self.loc = Vec(0, 0, 0)
        self.material = None
        self.direction = 0
        self.doors = []
