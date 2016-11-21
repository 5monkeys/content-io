# coding=utf-8
from __future__ import unicode_literals

from .environment import env
from .utils.formatters import ContentFormatter
from .utils.uri import URI
import six

empty = object()


class Node(object):

    _formatter = ContentFormatter()

    def __init__(self, uri, content=None, **meta):
        self.env = env.state
        self._uri = [uri, URI(uri)]
        self._content = [content]
        self.meta = meta

    def __repr__(self):
        return '<Node: %s>' % self.uri

    def __bytes__(self):
        content = self.render()
        if isinstance(content, six.text_type):
            content = content.encode('utf-8')
        return content or b''

    def __unicode__(self):
        return self.render() or ''

    __str__ = __bytes__ if six.PY2 else __unicode__

    def render(self, **context):
        if self.content is not None:
            if context:
                return self._formatter.format(self.content, **context)
            else:
                return self.content

    def get_uri(self):
        return self._uri[-1]

    def set_uri(self, uri):
        if uri != self.get_uri():
            self._uri.append(URI(uri))

    uri = property(get_uri, set_uri)

    def get_content(self):
        return self._content[-1]

    def set_content(self, content):
        if content != self.get_content():
            self._content.append(content)

    content = property(get_content, set_content)

    @property
    def initial(self):
        return self._content[0]

    @property
    def initial_uri(self):
        return self._uri[0]

    @property
    def namespace_uri(self):
        """
        Finds and returns first applied URI of this node that has a namespace.

        :return str: uri
        """
        try:
            return next(
                iter(filter(lambda uri: URI(uri).namespace, self._uri))
            )
        except StopIteration:
            return None

    def for_json(self):
        return {
            'uri': six.text_type(self.uri),
            'content': self.content,
            'meta': self.meta if self.meta is not None else {}
        }
