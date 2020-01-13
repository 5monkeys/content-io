# coding=utf-8
from __future__ import unicode_literals
from ..conf import settings
from collections import OrderedDict
import six
from six.moves.urllib.parse import unquote_plus, quote_plus


class URI(six.text_type):

    @staticmethod
    def __new__(cls, uri=None, scheme=None, namespace=None, path=None, ext=None, version=None, query=None):
        if isinstance(uri, URI):
            return uri
        elif uri is not None:
            return URI._parse(uri)
        else:
            return URI._render(scheme, namespace, path, ext, version, query)

    @classmethod
    def _parse(cls, uri):
        if isinstance(uri, six.binary_type):
            uri = uri.decode('utf-8')

        query = None
        base, _, version = uri.partition(settings.URI_VERSION_SEPARATOR)
        base, _, querystring = base.partition(settings.URI_QUERY_SEPARATOR)

        if querystring:
            query = OrderedDict()
            variable_pairs = querystring.split(settings.URI_QUERY_PARAMETER_SEPARATOR)
            for pair in variable_pairs:
                if not pair:
                    continue
                key, _, value = pair.partition(settings.URI_QUERY_VARIABLE_SEPARATOR)
                key = unquote(key)
                value = unquote(value)
                query[key] = [value] if value else []

        scheme, _, path = base.rpartition(settings.URI_SCHEME_SEPARATOR)
        namespace, _, path = path.rpartition(settings.URI_NAMESPACE_SEPARATOR)
        _path, _, ext = path.rpartition(settings.URI_EXT_SEPARATOR)
        if '/' in ext:
            ext = ''
        else:
            path = _path

        if not path and ext:
            path, ext = ext, ''

        return cls._render(
            scheme or settings.URI_DEFAULT_SCHEME,
            namespace or None,
            path,
            ext or None,
            version or None,
            query or None
        )

    @classmethod
    def _render(cls, scheme, namespace, path, ext, version, query):
        def parts_gen():
            if scheme:
                yield scheme
                yield settings.URI_SCHEME_SEPARATOR
            if namespace:
                yield namespace
                yield settings.URI_NAMESPACE_SEPARATOR
            if path:
                yield path
                if ext:
                    yield settings.URI_EXT_SEPARATOR
                    yield ext
                if query:
                    yield settings.URI_QUERY_SEPARATOR
                    for i, (key, value) in enumerate(query.items()):
                        if i:
                            yield settings.URI_QUERY_PARAMETER_SEPARATOR
                        yield quote(key)
                        yield settings.URI_QUERY_VARIABLE_SEPARATOR
                        if value:
                            yield quote(value[0])
                if version:
                    yield settings.URI_VERSION_SEPARATOR
                    yield version

        uri = six.text_type.__new__(cls, u''.join(parts_gen()))
        uri.scheme = scheme
        uri.namespace = namespace
        uri.path = path
        uri.ext = ext
        uri.version = version
        uri.query = dict(query) if query is not None else None
        return uri

    def is_absolute(self):
        """
        Validates that uri contains all parts except version
        """
        return self.namespace and self.ext and self.scheme and self.path

    def has_parts(self, *parts):
        return not any(getattr(self, part, None) is None for part in parts)

    def clone(self, **parts):
        part = lambda part: parts.get(part, getattr(self, part))
        args = (part(p) for p in ('scheme', 'namespace', 'path', 'ext', 'version', 'query'))
        return URI._render(*args)

    class Invalid(Exception):
        pass


def quote(string):
    if isinstance(string, six.text_type):
        string = string.encode('utf-8')
    return quote_plus(string)


def unquote(string):
    if six.PY2 and isinstance(string, six.text_type):
        string = unquote_plus(string.encode('utf-8'))
    else:
        string = unquote_plus(string)
    if isinstance(string, six.binary_type):
        string = string.decode('utf-8')
    return string
