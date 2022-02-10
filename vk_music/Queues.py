from queue import Queue
from time import sleep


class Queues:
    def __init__(self):
        self.queues = {}
        self.playing = {}
        self.sizes = {}

    def add(self, key, func):
        if self.queues.get(key):
            self.queues[key].put(func)
        else:
            self.queues[key] = Queue()
            self.queues[key].put(func)

    def get(self, key):
        sleep(3)
        self.add_size(key, -1)
        if self.queues.get(key):
            return self.queues[key].get()
        self.set_playing(key, False)
        return lambda: 0

    def add_size(self, key, size=1):
        self.sizes[key] = self.sizes.get(key, 0) + size
        return self.sizes[key]

    def is_playing(self, key):
        return self.playing.get(key, False)

    def set_playing(self, key, val):
        self.playing[key] = val
