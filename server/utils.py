import time
from flask import url_for as _url_for, current_app, _request_ctx_stack

import threading
import numpy as np
from queue import Queue


def timestamp():
    """Return the current timestamp as an integer"""
    return int(time.time())


def url_for(*args, **kwargs):
    """
    url_for replacement that works even when there is no request context.
    """
    if '_external' not in kwargs:
        kwargs['_external'] = False
    reqctx = _request_ctx_stack.top
    if reqctx is None:
        if kwargs['_external']:
            raise RuntimeError('Cannot generate external URLs without a '
                               'request context.')
        with current_app.test_request_context():
            return _url_for(*args, **kwargs)
    return _url_for(*args, **kwargs)


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
