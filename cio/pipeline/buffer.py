# coding=utf-8
from __future__ import unicode_literals

from collections import defaultdict
from ..node import Node
from ..utils.thread import ThreadLocalObject


class BufferedNode(Node):

    def __init__(self, node, callback):
        self._node = node
        self._callback = callback
        self._flushed = False

    def __repr__(self):
        return '<BufferedNode: %s>' % self.uri

    def flush(self):
        if not self._flushed:
            self._callback()

    @property
    def uri(self):
        self.flush()
        return self._node.uri

    def get_content(self):
        self.flush()
        return self._node.content

    def set_content(self, content):
        self._flushed = True
        self._node.content = content

    content = property(get_content, set_content)

    @property
    def meta(self):
        return self._node.meta

    @property
    def initial(self):
        return self._node.initial

    @property
    def initial_uri(self):
        return self._node.initial_uri


class NodeBuffer(ThreadLocalObject):

    def __init__(self):
        super(NodeBuffer, self).__init__()
        self._buffer = {}

    def __len__(self):
        return sum(len(method_nodes) for method_nodes in self._buffer.values())

    def add(self, method, node):
        if method not in self._buffer:
            self._buffer[method] = defaultdict(list)

        buffer = self._buffer[method]
        buffer[node.initial_uri].append(node)

    def pop(self, method):
        buffered_nodes = dict(self._buffer[method])
        self._buffer[method].clear()
        return buffered_nodes

    def clear(self):
        self._buffer.clear()
