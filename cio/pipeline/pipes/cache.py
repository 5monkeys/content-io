# coding=utf-8
from __future__ import unicode_literals

import six
from .base import BasePipe
from ...conf import settings
from ...backends import cache


class CachePipe(BasePipe):

    def get_request(self, request):
        response = {}

        # Only get nodes from cache without specified version
        uris = tuple(uri for uri, node in six.iteritems(request) if not node.uri.version)

        if uris:
            cached_nodes = cache.get_many(uris)

            for uri, cached_node in six.iteritems(cached_nodes):
                node = response[node.uri] = request.pop(uri)
                self.materialize_node(node, **cached_node)

        return response

    def get_response(self, response):
        nodes = {}

        # Cache nodes without specified version (i.e. default or published)
        for uri, node in six.iteritems(response):
            if not uri.version:
                origin_uri = node.uri.clone(namespace=uri.namespace)
                nodes[origin_uri] = node.content
                # Empty node meta to be coherent with cached nodes
                node.meta.clear()

        pipe_config = settings.CACHE.get('PIPE', {})
        cache_on_get = pipe_config.get('CACHE_ON_GET', True)

        if nodes and cache_on_get:
            cache.set_many(nodes)

        return response

    def publish_response(self, response):
        nodes = dict((node.uri, node.content) for uri, node in six.iteritems(response))
        cache.set_many(nodes)
        return response

    def delete_response(self, response):
        cache.delete_many(response.keys())
        return response
