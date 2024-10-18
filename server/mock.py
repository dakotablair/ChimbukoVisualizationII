class MockDB:
    Model = object
    Integer = None
    Float = None
    PickleType = None

    def Column(self, *args, **kwargs):
        pass

    def String(self):
        pass


class MockPDB():
    def __init__(self, collections=None):
        self.pdb_collections = collections


class MockPDBCollection():
    def __init__(self, items=None):
        self.items = items or []

    def filter(self, predicate):
        test = None
        if callable(predicate):
            test = predicate
        return filter(test, self.items)


class MockSocketIO():
    def on(self, *args, **kwargs):
        def wrap(*args, **kwargs):
            pass
        return wrap
