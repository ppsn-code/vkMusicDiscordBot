class Queues:
    def __init__(self):
        self.queues = {}

    def add(self, key, func):
        if self.queues.get(key):
            self.queues[key].append(func)
        else:
            self.queues[key] = [func]

    def get(self, key):
        if self.queues.get(key):
            ret = self.queues[key].pop(0)
            print(ret)
            return ret
        return self.pass_func

    @staticmethod
    def pass_func():
        pass
