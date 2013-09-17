from .environment import env
from .utils.uri import URI

empty = object()


class Node(object):

    def __init__(self, uri, content=None, **meta):
        self.env = env.state
        self._uri = [uri, URI(uri)]
        self._content = [content]
        self.meta = meta

    def __repr__(self):
        return u'<Node: %s>' % self.uri

    def __str__(self):
        content = self.render()
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        return content or ''

    def __unicode__(self):
        return self.render() or u''

    def render(self, **context):
        if self.content is not None:
            if context:
                return self.content.format(**context)
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

    def for_json(self):
        return {
            'uri': str(self.uri),
            'content': self.content,
            'meta': self.meta if self.meta is not None else {}
        }
