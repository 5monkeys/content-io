from .base import BasePipe
from ...backends import cache


class CachePipe(BasePipe):

    def get_request(self, request):
        response = {}

        # Only get nodes from cache without specified version
        uris = tuple(uri for uri, node in request.iteritems() if not node.uri.version)

        if uris:
            cached_nodes = cache.get_many(uris)

            for uri, cached_node in cached_nodes.iteritems():
                node = response[node.uri] = request.pop(uri)
                self.materialize_node(node, **cached_node)

        return response

    def get_response(self, response):
        nodes = {}

        # Cache nodes without specified version (i.e. default or published)
        for uri, node in response.iteritems():
            if not uri.version:
                origin_uri = node.uri.clone(namespace=uri.namespace)
                nodes[origin_uri] = node.content
                # Empty node meta to be coherent with cached nodes
                node.meta.clear()

        if nodes:
            cache.set_many(nodes)

        return response

    def publish_response(self, response):
        nodes = dict((node.uri, node.content) for uri, node in response.iteritems())
        cache.set_many(nodes)
        return response

    def delete_response(self, response):
        cache.delete_many(response.keys())
        return response
