# coding=utf-8
from __future__ import unicode_literals

from .base import BasePipe
from ...conf.exceptions import ImproperlyConfigured
from ...node import empty
from ...plugins import plugins
from ...plugins.exceptions import UnknownPlugin


class PluginPipe(BasePipe):

    def render_response(self, response):
        for node in response.values():
            try:
                plugin = plugins.resolve(node.uri)
            except UnknownPlugin:
                raise ImproperlyConfigured('Unknown plugin "%s" or improperly configured pipeline for node "%s".' % (
                    node.uri.ext,
                    node.uri
                ))
            else:
                data = plugin.load(node.content)
                node.content = plugin.render(data)

        return response

    def get_response(self, response):
        return self.render_response(response)

    def set_request(self, request):
        for node in request.values():
            try:
                plugin = plugins.resolve(node.uri)
            except UnknownPlugin:
                pass
                # TODO: Should we maybe raise here?
            else:
                node.content = plugin.save(node.content)

    def set_response(self, response):
        return self.render_response(response)

    def publish_response(self, response):
        return self.render_response(response)

    def delete_response(self, response):
        for node in response.values():
            try:
                plugin = plugins.resolve(node.uri)
                if node.content is not empty:
                    plugin.delete(node.content)
            except UnknownPlugin:
                pass
                # TODO: Should we maybe raise here?

        return response
