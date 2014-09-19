# coding=utf-8
from __future__ import unicode_literals

import six
from .exceptions import UnknownPlugin
from ..conf import settings
from ..utils.imports import import_class
from ..utils.uri import URI


class PluginLibrary(object):

    def __init__(self):
        self._plugins = {}
        settings.watch(self.load)

    def __iter__(self):
        return six.iterkeys(self.plugins)

    @property
    def plugins(self):
        if not self._plugins:
            self.load()
        return self._plugins

    def load(self):
        self._plugins = {}
        for plugin_path in settings.PLUGINS:
            self.register(plugin_path)

    def register(self, plugin):
        if isinstance(plugin, six.string_types):
            try:
                plugin_class = import_class(plugin)
                self.register(plugin_class)
            except ImportError as e:
                raise ImportError('Could not import content-io plugin "%s" (Is it on sys.path?): %s' % (plugin, e))
        else:
            self._plugins[plugin.ext] = plugin()

    def get(self, ext):
        if ext not in self.plugins:
            raise UnknownPlugin
        return self.plugins[ext]

    def resolve(self, uri):
        uri = URI(uri)
        return self.get(uri.ext)


plugins = PluginLibrary()
