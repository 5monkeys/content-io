import logging
import six
from contextlib import contextmanager
from types import ModuleType
from . import default_settings

logger = logging.getLogger(__name__)


class Settings(dict):

    def __init__(self, conf=None, **settings):
        self._listeners = set()
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
        for key, value in six.iteritems(self):
            if isinstance(value, dict):
                value = dict(value)
            if isinstance(value, list):
                value = list(value)
            copy[key] = value
        return copy

    def configure(self, conf=None, **settings):
        if isinstance(conf, ModuleType):
            conf = conf.__dict__

        for setting, value in six.iteritems(conf or settings):
            if setting.isupper():
                self[setting] = value

        for callback in self._listeners:
            try:
                callback()
            except Exception as e:
                logger.warn('Failed to notify callback about new settings; %s', e)

    def watch(self, callback):
        self._listeners.add(callback)

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


settings = Settings(default_settings)
