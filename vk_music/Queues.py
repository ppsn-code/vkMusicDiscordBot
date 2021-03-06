from queue import Queue


class Queues:
    def __init__(self):
        self.queues = {}
        self.sizes = {}
        self.looped = {}
        self.playing = {}

    def add(self, key, func):
        if self.queues.get(key):
            self.queues[key].put(func)
        else:
            self.queues[key] = Queue()
            self.queues[key].put(func)

    def is_looped(self, key):
        return self.looped.get(key, False)

    def set_loop(self, key, val):
        self.looped[key] = val

    def remove(self, key):
        if self.queues.get(key) is not None:
            del self.queues[key]

        if self.playing.get(key) is not None:
            del self.playing[key]

        if self.sizes.get(key) is not None:
            del self.sizes[key]

    def get(self, key):
        self.set_playing(key, False)
        if self.queues.get(key) and not self.queues[key].empty():
            self.add_size(key, -1)
            return self.queues[key].get()
        return lambda: 0

    def set_playing(self, key, val):
        self.playing[key] = val

    def is_playing(self, key):
        return self.playing.get(key, False)

    def add_size(self, key, size=1):
        self.sizes[key] = self.sizes.get(key, 0) + size
        return self.sizes[key]
