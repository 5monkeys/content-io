# coding=utf-8
from __future__ import unicode_literals

from cio.conf import settings


class BasePlugin(object):

    ext = None

    @property
    def settings(self):
        return settings.get(self.ext.upper(), {})

    def load(self, content):
        """
        Return plugin data for content string
        """
        return content

    def save(self, data):
        """
        Persist external plugin resources and return content string for plugin data
        """
        return data

    def delete(self, data):
        """
        Delete external plugin resources
        """
        pass

    def render(self, data):
        """
        Render plugin
        """
        return data
