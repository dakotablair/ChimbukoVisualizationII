from runstats import Statistics
from collections import defaultdict
import threading


class MessageStats(object):
    def __init__(self):
        self.stats = defaultdict(lambda: Statistics())
        self.lock = threading.Lock()

    def update(self, key, data):
        with self.lock:
            for num in data:
                self.stats[key].push(num)

    def get(self, key):
        with self.lock:
            return self.stats[key].mean(), self.stats[key].stddev()
