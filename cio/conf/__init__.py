# coding=utf-8
from __future__ import unicode_literals

import logging
import six
from contextlib import contextmanager
from types import ModuleType
from . import default_settings
from ..utils.thread import ThreadLocalObject

logger = logging.getLogger(__name__)


class LocalSettings(ThreadLocalObject):

    def __init__(self, base):
        super(LocalSettings, self).__init__()
        self._base = base
        self._local = {}

    def __contains__(self, key):
        return key in self._local

    def get(self, var):
        return self._local[var]

    def set(self, **vars):
        def deepupdate(original, update):
            for key, value in six.iteritems(original):
                if key not in update:
                    update[key] = value
                elif isinstance(value, dict):
                    deepupdate(value, update[key])
            return update

        for setting, value in six.iteritems(vars):
            if isinstance(value, dict):
                base_value = self._base.get(setting)
                if base_value and isinstance(base_value, dict):
                    deepupdate(base_value, value)

            self._local[setting] = value


class Settings(dict):

    def __init__(self, conf=None, **settings):
        super(Settings, self).__init__()
        self._listeners = set()
        self._local = LocalSettings(self)
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

    def configure(self, conf=None, local=False, **settings):
        if isinstance(conf, ModuleType):
            conf = conf.__dict__

        if local:
            self._local.set(**conf or settings)

        else:
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

    def __getitem__(self, key):
        """
        First try environment specific setting, then this config
        """
        if key in self._local:
            return self._local.get(key)

        return super(Settings, self).__getitem__(key)

    __getattr__ = __getitem__

    def __setattr__(self, name, value):
        if name.isupper():
            self[name] = value
        else:
            super(Settings, self).__setattr__(name, value)


settings = Settings(default_settings)
