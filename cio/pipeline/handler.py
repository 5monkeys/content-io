# coding=utf-8
from __future__ import unicode_literals

import logging
from collections import defaultdict
from functools import partial
from .buffer import NodeBuffer, BufferedNode
from .history import NodeHistory
from ..conf import settings
from ..utils.imports import import_class

logger = logging.getLogger(__name__)

PIPELINE_CALLS = ('get', 'set', 'delete', 'publish')


class PipelineHandler(object):

    def __init__(self):
        self.history = NodeHistory()
        self._buffer = NodeBuffer()
        self.load()
        settings.watch(self.load)

    def load(self):
        self.pipes = []
        for pipe_path in settings.PIPELINE:
            self.add_pipe(pipe_path)
        self.build()

    def add_pipe(self, pipe):
        try:
            if isinstance(pipe, type):
                pipe_class = pipe
            else:
                pipe_class = import_class(pipe)
        except ImportError as e:
            raise ImportError('Could not import content-io pipe "%s" (Is it on sys.path?): %s' % (pipe, e))
        else:
            self.pipes.append(pipe_class)

    def build(self):
        self._pipeline = defaultdict(list)
        for pipe_class in self.pipes:
            pipe = pipe_class()
            for call in PIPELINE_CALLS:
                request_handler = getattr(pipe, '%s_request' % call, None)
                response_handler = getattr(pipe, '%s_response' % call, None)
                self._pipeline[call].append((request_handler, response_handler))

    def send(self, method, *nodes):
        request = dict((node.uri, node) for node in nodes)
        response_chain = []

        # Iterate request chain
        for request_handler, response_handler in self._pipeline[method]:
            if request_handler:
                pipe_response = request_handler(request)
            else:
                pipe_response = None

            # Build response chain
            response_chain.append((response_handler, pipe_response))

            # Go no further in pipeline if out of node requests
            if not request:
                break

        # Turn request to response
        response = request

        # Iterate response chain
        for response_handler, pipe_response in reversed(response_chain):
            if response and response_handler:
                response = response_handler(response)
            if pipe_response:
                response.update(pipe_response)

        # Log response
        self.history.log(method, *response.values())

        return response

    def buffer(self, method, node):
        callback = partial(self.flush, method)
        buffered_node = BufferedNode(node, callback=callback)
        self._buffer.add(method, buffered_node)
        return buffered_node

    def flush(self, method, sender=None):
        # Extract nodes from buffer
        buffer = self._buffer.pop(method)

        # Re-buffer triggering node if buffer for some reason is empty
        if not buffer:
            logger.warn(
                'Tried to flush empty buffer, '
                'triggered by probably abandoned or cached node: %r',
                sender
            )
            self._buffer.add(method, sender)
            buffer = self._buffer.pop(method)

        # Extract and flatten wrapped nodes, send only distinct uri's
        nodes = (buffered_nodes[0]._node for buffered_nodes in buffer.values())

        # Send nodes through pipeline
        response = self.send(method, *nodes)

        # Update buffered nodes to make sure uri duplicates,
        # not sent through pipeline, gets content
        for node in response.values():
            for buffered_node in buffer[node.initial_uri]:
                buffered_node.content = node.content

    def clear(self):
        self._buffer.clear()
        self.history.clear()
