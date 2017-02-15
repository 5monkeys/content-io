# coding=utf-8
from __future__ import unicode_literals

import six
from ..base import CacheBackend


class LocMemCacheBackend(CacheBackend):

    scheme = 'locmem'

    def __init__(self, **config):
        super(LocMemCacheBackend, self).__init__(**config)
        self._cache = {}
        self.calls = 0
        self.hits = 0
        self.misses = 0
        self.sets = 0

    def clear(self):
        self._cache.clear()

    def _get(self, key):
        value = self._cache.get(key)
        self.calls += 1
        if value is None:
            self.misses += 1
        else:
            self.hits += 1
        return value

    def _get_many(self, keys):
        result = {}
        for key in keys:
            value = self._cache.get(key)
            if value is not None:
                result[key] = value
                self.hits += 1
            else:
                self.misses += 1
        self.calls += 1
        return result

    def _set(self, key, value):
        self._cache[key] = value
        self.calls += 1
        self.sets += 1

    def _set_many(self, data):
        for key, value in six.iteritems(data):
            self._cache[key] = value
            self.sets += 1
        self.calls += 1

    def _delete(self, key):
        if key in self._cache:
            del self._cache[key]
        self.calls += 1

    def _delete_many(self, keys):
        for key in keys:
            self._delete(key)
            self.calls -= 1  # Revert individual _delete call count
        self.calls += 1
