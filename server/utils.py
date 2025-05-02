import time


def timestamp():
    """Return the current timestamp in milli-second as an integer"""
    return int(round(time.time() * 1000))
