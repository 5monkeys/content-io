# coding=utf-8
from __future__ import unicode_literals

from ..conf import settings
import six


class URI(six.text_type):

    @staticmethod
    def __new__(cls, uri=None, scheme=None, namespace=None, path=None, ext=None, version=None):
        if isinstance(uri, URI):
            return uri
        elif uri is not None:
            return URI._parse(uri)
        else:
            return URI._render(scheme, namespace, path, ext, version)

    @classmethod
    def _parse(cls, uri):
        base, _, version = uri.partition(settings.URI_VERSION_SEPARATOR)
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
            scheme or 'i18n',
            namespace or None,
            path,
            ext or None,
            version or None
        )

    @classmethod
    def _render(cls, scheme, namespace, path, ext, version):
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
                if version:
                    yield settings.URI_VERSION_SEPARATOR
                    yield version

        uri = six.text_type.__new__(cls, ''.join(parts_gen()))
        uri.scheme = scheme
        uri.namespace = namespace
        uri.path = path
        uri.ext = ext
        uri.version = version
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
        args = (part(p) for p in ('scheme', 'namespace', 'path', 'ext', 'version'))
        return URI._render(*args)

    class Invalid(Exception):
        pass
