from threading import local


class ThreadLocalObject(local):
    """
    Base class to inherit from when thread local instances are needed.
    """
    initialized = False

    def __init__(self):
        if self.initialized:
            raise SystemError('%s initialized too many times' % self.__class__.__name__)
        self.initialized = True
