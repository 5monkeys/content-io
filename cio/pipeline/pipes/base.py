# coding=utf-8
from __future__ import unicode_literals


class BasePipe(object):
    """
    Optional implementable pipe methods:

    def get_request(self, request):
        pass

    def get_response(self, response):
        return response

    def set_request(self, request):
        pass

    def set_response(self, response):
        return response

    def delete_request(self, request):
        pass

    def delete_response(self, response):
        return response

    def publish_request(self, request):
        pass

    def publish_response(self, response):
        return response
    """

    def materialize_node(self, node, uri, content, meta=None):
        """
        Set node uri and content from backend
        """
        node.uri = uri
        node.content = content
        node.meta = meta if meta is not None else {}
