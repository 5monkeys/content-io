# coding=utf-8
from __future__ import unicode_literals

import six
from collections import namedtuple
from contextlib import contextmanager
from .conf import settings
from .utils.thread import ThreadLocalObject

DEFAULT = 'default'
State = namedtuple('State', ['i18n', 'l10n', 'g11n'])


class Environment(ThreadLocalObject):

    def __init__(self):
        super(Environment, self).__init__()
        self.reset()
        settings.watch(self.reset)

    @contextmanager
    def __call__(self, name=None, i18n=None, l10n=None, g11n=None):
        if name:
            self.push(name)
        else:
            self.push_state(i18n=i18n, l10n=l10n, g11n=g11n)
        yield
        self.pop()

    def reset(self):
        self._stack = []
        self.push(DEFAULT)

    def push(self, name):
        env = settings.ENVIRONMENT[name]
        self.push_state(**env)

    def _ensure_tuple(self, ns):
        if isinstance(ns, tuple):
            return ns
        elif isinstance(ns, six.string_types):
            return ns,
        elif hasattr(ns, '__iter__'):
            return tuple(ns)
        else:
            return ns,

    def push_state(self, i18n=None, l10n=None, g11n=None):
        i18n = self._ensure_tuple(i18n or self.i18n)
        l10n = self._ensure_tuple(l10n or self.l10n)
        g11n = self._ensure_tuple(g11n or self.g11n)
        state = State(i18n, l10n, g11n)
        self._stack.append(state)

    def pop(self):
        if len(self._stack) == 1:
            raise IndexError('Unable to pop last environment state')
        self._stack.pop()

    @property
    def state(self):
        return self._stack[-1]

    @property
    def i18n(self):
        return self.state.i18n

    @property
    def l10n(self):
        return self.state.l10n

    @property
    def g11n(self):
        return self.state.g11n


env = Environment()
