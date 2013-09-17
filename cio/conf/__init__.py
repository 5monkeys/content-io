from . import default_settings
from contextlib import contextmanager
from types import ModuleType


class Settings(dict):

    def __init__(self, conf=None, **settings):
        self.configure(conf=conf, **settings)

    @contextmanager
    def __call__(self, **settings):
        state = self.deepcopy()
        self.configure(**settings)
        yield
        self.clear()
        self.update(state)

    def deepcopy(self):
        copy = {}
        for key, value in self.iteritems():
            if isinstance(value, dict):
                value = dict(value)
            if isinstance(value, list):
                value = list(value)
            copy[key] = value
        return copy

    def configure(self, conf=None, **settings):
        if isinstance(conf, ModuleType):
            conf = conf.__dict__

        for setting, value in (conf or settings).iteritems():
            if setting.isupper():
                self[setting] = value

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


settings = Settings(default_settings)
