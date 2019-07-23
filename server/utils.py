import time
import threading
import numpy as np
from queue import Queue


class MessageGenerator(object):
    def __init__(self, n=100, size=1024 * 1024, interval=1000):
        self.n = n                # total number of messages
        self.size = size          # message size in bytes
        self.interval = interval  # interval between messages in millisecond

        self.mean = float(np.random.randint(0, 100))
        self.std_dev = float(np.random.randint(10, 50))
        self.count = int(self.size / 4)  # number of elements in a message

        # thread
        self.q = Queue()  # message queue
        self.ev = threading.Event()  # terminating event
        self.thread = threading.Thread(target=self._run)

    def _run(self):
        count = 0
        while count < self.n:
            # generate random data (normal distribution)
            t_begin = time.time()
            rd = np.random.normal(
                self.mean, self.std_dev, self.count).astype(np.float32)
            rd = rd.tolist()
            t_end = time.time()

            # make interval
            t_elapsed = t_end - t_begin
            if t_elapsed < self.interval / 1000:
                time.sleep(self.interval / 1000 - t_elapsed)

            # add to queue
            self.q.put(rd)
            count = count + 1

    def start(self):
        self.thread.start()

    def get(self):
        rd = self.q.get()
        self.q.task_done()
        return rd
