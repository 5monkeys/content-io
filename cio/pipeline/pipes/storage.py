# coding=utf-8
from __future__ import unicode_literals

import six
from .base import BasePipe
from ...conf import settings
from ...backends import storage
from ...backends.exceptions import NodeDoesNotExist


class StoragePipe(BasePipe):

    def get_request(self, request):
        response = {}
        stored_nodes = storage.get_many(request.keys())

        for uri, stored_node in six.iteritems(stored_nodes):
            node = response[node.uri] = request.pop(uri)
            self.materialize_node(node, **stored_node)

        return response

    def get_response(self, response):
        if response:
            # Redirect nodes without extension (non-persisted) to default
            for node in response.values():
                if not node.uri.ext:
                    node.uri = node.uri.clone(ext=settings.URI_DEFAULT_EXT)

        return response

    def set_request(self, request):
        for node in request.values():
            stored_node, _ = storage.set(node.uri, node.content, **node.meta)
            uri = stored_node['uri']
            node.uri = uri
            node.meta = stored_node['meta']

    def delete_request(self, request):
        deleted_nodes = storage.delete_many(request.keys())

        for uri, deleted_node in six.iteritems(deleted_nodes):
            node = request[uri]
            deleted_node['content'] = None  # Set content to None to signal node has been deleted
            self.materialize_node(node, **deleted_node)

    def publish_request(self, request):
        for uri, node in list(request.items()):
            try:
                published_node = storage.publish(uri, **node.meta)
            except NodeDoesNotExist:
                request.pop(uri)
            else:
                node = request[uri]
                self.materialize_node(node, **published_node)


class NamespaceFallbackPipe(BasePipe):

    def get_request(self, request):
        response = {}
        fallback_uris = {}

        # Build fallback URI map
        for uri, node in six.iteritems(request):
            # if node.uri != node.initial_uri:
            namespaces = getattr(node.env, uri.scheme)[1:]
            if namespaces:
                uris = [uri.clone(namespace=namespace) for namespace in namespaces]
                fallback_uris[node.uri] = uris

        # Fetch nodes from storage, each fallback level slice at a time
        while fallback_uris:
            level_uris = dict((fallback.pop(0), uri) for uri, fallback in six.iteritems(fallback_uris))
            stored_nodes = storage.get_many(level_uris.keys())

            # Set node fallback content and add to response
            for uri, stored_node in six.iteritems(stored_nodes):
                requested_uri = level_uris[uri]
                node = response[node.uri] = request.pop(requested_uri)
                self.materialize_node(node, **stored_node)

            # Remove exhausted uris that has run out of fallback namespaces
            for uri, fallback in list(fallback_uris.items()):
                if not fallback:
                    fallback_uris.pop(uri)

        return response
