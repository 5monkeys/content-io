# coding=utf-8
from __future__ import unicode_literals

import inspect
import six
from .base import BaseBackend, CacheBackend, StorageBackend
from .exceptions import InvalidBackend
from ..conf import settings
from ..utils.imports import import_class
from ..utils.uri import URI

BACKENDS = {
    'locmem': 'locmem',
    'sqlite': 'sqlite'
}


def get_backend(backend):
    config = {}

    # Unpack backend dict format
    if isinstance(backend, dict):
        _backend = backend.get('BACKEND')
        config.update(backend)
        backend = _backend

    if inspect.isclass(backend) and issubclass(backend, BaseBackend):
        backend_class = backend
    else:
        # Parse uri or package
        if '://' in backend:
            config['BACKEND'] = backend

            scheme, _config = backend.split('://', 1)
            if scheme not in BACKENDS:
                raise InvalidBackend('Invalid content-io backend scheme "%s"' % scheme)
            package = 'cio.backends.%s' % BACKENDS[scheme]
            class_name = 'Backend'

            # Parse config
            name, _, params = _config.partition('?')
            if name:
                config['NAME'] = name
            if params:
                config.update(dict(param.split('=') for param in params.split('&')))
        elif '.' in backend:
            package, class_name = backend.rsplit('.', 1)
        else:
            raise InvalidBackend('Invalid content-io backend "%s"' % backend)

        # Import and instantiate backend
        try:
            backend_class = import_class(package, class_name)
        except ImportError as e:
            raise ImportError('Could not import content-io backend "%s" (Is it on sys.path?): %s' % (backend, e))

    return backend_class(**config)


class BackendManager(object):
    """
    Manager for backend. Handles arg validation.
    """
    def __init__(self):
        self._backend = None
        settings.watch(self.setup)

    @property
    def backend(self):
        if not self._backend:
            self.setup()

        return self._backend

    def setup(self):
        # Find and instantiate backend
        config = self._get_backend_config()
        backend = get_backend(config)

        # Validate backend
        if self._is_valid_backend(backend):
            self._backend = backend
            self._update_backend_settings(backend.config)
        else:
            raise InvalidBackend('Invalid content-io %s backend "%s"' % (self._scope(), self._conf))

    def _scope(self):
        return self.__class__.__name__.rstrip('Manager').lower()

    def _get_backend_config(self):
        raise NotImplementedError  # pragma: no cover

    def _update_backend_settings(self, config):
        raise NotImplementedError  # pragma: no cover

    def _is_valid_backend(self, backend):
        raise NotImplementedError  # pragma: no cover

    def _clean_get_uri(self, uri):
        raise NotImplementedError  # pragma: no cover

    def _clean_set_uri(self, uri):
        raise NotImplementedError  # pragma: no cover

    def _clean_delete_uri(self, uri):
        raise NotImplementedError  # pragma: no cover

    def _clean_get_uris(self, uris):
        return tuple(self._clean_get_uri(uri) for uri in uris)

    def _clean_set_uris(self, uris):
        return tuple(self._clean_set_uri(uri) for uri in uris)

    def _clean_delete_uris(self, uris):
        return tuple(self._clean_delete_uri(uri) for uri in uris)

    def _clean_uri(self, uri, *parts):
        uri = URI(uri)
        if not uri.has_parts(*parts):
            raise URI.Invalid('Invalid URI "%s"; must contain %s.' % (uri, ', '.join(parts)))
        return uri


class CacheManager(BackendManager, CacheBackend):

    def _get_backend_config(self):
        return settings.CACHE

    def _update_backend_settings(self, config):
        settings.CACHE = config

    def get(self, uri):
        uri = self._clean_get_uri(uri)
        return self.backend.get(uri)

    def get_many(self, uris):
        uris = self._clean_get_uris(uris)
        return self.backend.get_many(uris)

    def set(self, uri, content):
        uri = self._clean_set_uri(uri)
        self.backend.set(uri, content)

    def set_many(self, nodes):
        nodes = dict((self._clean_set_uri(uri), content) for uri, content in six.iteritems(nodes))
        self.backend.set_many(nodes)

    def delete(self, uri):
        uri = self._clean_delete_uri(uri)
        self.backend.delete(uri)

    def delete_many(self, uris):
        uris = self._clean_delete_uris(uris)
        self.backend.delete_many(uris)

    def clear(self):
        self.backend.clear()

    def _is_valid_backend(self, backend):
        return isinstance(backend, CacheBackend)

    def _clean_get_uri(self, uri):
        return self._clean_uri(uri, 'namespace', 'path')

    def _clean_set_uri(self, uri):
        return self._clean_uri(uri, 'namespace', 'path', 'ext')

    def _clean_delete_uri(self, uri):
        return self._clean_uri(uri, 'namespace', 'path')


class StorageManager(BackendManager, StorageBackend):

    def _get_backend_config(self):
        return settings.STORAGE

    def _update_backend_settings(self, config):
        settings.STORAGE = config

    def get(self, uri):
        uri = self._clean_get_uri(uri)
        return self.backend.get(uri)

    def get_many(self, uris):
        uris = self._clean_get_uris(uris)
        return self.backend.get_many(uris)

    def set(self, uri, content, **meta):
        uri = self._clean_set_uri(uri)

        if content is None:
            raise ValueError('Can not persist content equal to None for URI "%s".' % uri)

        return self.backend.set(uri, content, **meta)

    def delete(self, uri):
        uri = self._clean_delete_uri(uri)
        return self.backend.delete(uri)

    def delete_many(self, uris):
        uris = self._clean_delete_uris(uris)
        return self.backend.delete_many(uris)

    def publish(self, uri, **meta):
        uri = self._clean_publish_uri(uri)
        return self.backend.publish(uri, **meta)

    def get_revisions(self, uri):
        uri = self._clean_get_uri(uri)
        return self.backend.get_revisions(uri)

    def search(self, uri=None):
        _uri = URI(uri)
        if not uri or settings.URI_SCHEME_SEPARATOR not in uri:
            _uri = _uri.clone(scheme=None)
        return self.backend.search(uri=_uri)

    def _is_valid_backend(self, backend):
        return isinstance(backend, StorageBackend)

    def _clean_get_uri(self, uri):
        return self._clean_uri(uri, 'namespace', 'path')

    def _clean_set_uri(self, uri):
        return self._clean_uri(uri, 'namespace', 'path', 'ext', 'version')

    def _clean_delete_uri(self, uri):
        return self._clean_uri(uri, 'namespace', 'path', 'version')

    def _clean_publish_uri(self, uri):
        return self._clean_uri(uri, 'namespace', 'path', 'version')


cache = CacheManager()
storage = StorageManager()
