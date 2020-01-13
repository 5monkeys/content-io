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
                data = plugin.load_node(node)
                node.content = plugin.render_node(node, data)

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
                node = plugin.save_node(node)

    def set_response(self, response):
        return self.render_response(response)

    def publish_request(self, request):
        for uri, node in list(request.items()):
            try:
                plugin = plugins.resolve(uri)
            except UnknownPlugin:
                pass
                # TODO: Should we maybe raise here?
            else:
                node = plugin.publish_node(node)

    def publish_response(self, response):
        return self.render_response(response)

    def delete_response(self, response):
        for node in response.values():
            try:
                plugin = plugins.resolve(node.uri)
                if node.content is not empty:
                    plugin.delete_node(node)
            except UnknownPlugin:
                pass
                # TODO: Should we maybe raise here?

        return response
