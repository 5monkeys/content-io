# coding=utf-8
from __future__ import unicode_literals

import json
import logging
import six
from hashlib import sha1
from .exceptions import NodeDoesNotExist
from ..utils.uri import URI

logger = logging.getLogger(__name__)


class BaseBackend(object):

    scheme = None

    def __init__(self, **config):
        self.config = config


class CacheBackend(BaseBackend):

    NONE = '__None__'

    def get(self, uri):
        """
        Return node for uri or None if not exists:
            {uri: x, content: y}
        """
        cache_key = self._build_cache_key(uri)
        value = self._get(cache_key)
        if value is not None:
            return self._decode_node(uri, value)

    def get_many(self, uris):
        """
        Return request uri map of found nodes as dicts:
            {requested_uri: {uri: x, content: y}}
        """
        cache_keys = dict((self._build_cache_key(uri), uri) for uri in uris)
        result = self._get_many(cache_keys)
        nodes = {}
        for cache_key in result:
            uri = cache_keys[cache_key]
            value = result[cache_key]
            node = self._decode_node(uri, value)
            if node:
                nodes[uri] = node
        return nodes

    def set(self, uri, content):
        """
        Cache node content for uri.
        No return.
        """
        key, value = self._prepare_node(uri, content)
        self._set(key, value)

    def set_many(self, nodes):
        """
        Takes nodes dict {uri: content, ...} as argument.
        No return.
        """
        data = self._prepare_nodes(nodes)
        self._set_many(data)

    def delete(self, uri):
        """
        Remove node uri from cache.
        No return.
        """
        cache_key = self._build_cache_key(uri)
        self._delete(cache_key)

    def delete_many(self, uris):
        """
        Remove many nodes from cache.
        No return.
        """
        cache_keys = (self._build_cache_key(uri) for uri in uris)
        self._delete_many(cache_keys)

    def clear(self):
        """
        Removes all nodes from cache
        """
        raise NotImplementedError  # pragma: no cover

    def _build_cache_key(self, uri):
        """
        Build sha1 hex cache key to handle key length and whitespace to be compatible with Memcached
        """
        key = uri.clone(ext=None, version=None)

        if six.PY3:
            key = key.encode('utf-8')

        return sha1(key).hexdigest()

    def _get(self, key):
        raise NotImplementedError  # pragma: no cover

    def _get_many(self, keys):
        raise NotImplementedError  # pragma: no cover

    def _set(self, key, value):
        raise NotImplementedError  # pragma: no cover

    def _set_many(self, data):
        raise NotImplementedError  # pragma: no cover

    def _delete(self, key):
        raise NotImplementedError  # pragma: no cover

    def _delete_many(self, keys):
        raise NotImplementedError  # pragma: no cover

    def _encode_content(self, uri, content):
        """
        Encode/pack node uri and content in a way that the cache backend are able to persist.
        """
        return uri, content

    def _decode_content(self, content):
        """
        Decode/unpack cached node to uri and unicode content.
        """
        uri, content = content
        return uri, content

    def _decode_node(self, uri, content):
        _uri, _content = self._decode_content(content)
        if _uri:
            _uri = URI(_uri)
            if uri.ext in (None, _uri.ext):  # Validate plugin
                return {
                    'uri': _uri,
                    'content': _content
                }

    def _prepare_node(self, uri, content):
        key = self._build_cache_key(uri)
        value = self._encode_content(uri, content)
        return key, value

    def _prepare_nodes(self, nodes):
        return dict(self._prepare_node(uri, content) for uri, content in six.iteritems(nodes))


class StorageBackend(BaseBackend):

    def get(self, uri):
        """
        Return node for uri or raise NodeDoesNotExist:
            {uri: x, content: y, meta: {}}
        """
        raise NotImplementedError  # pragma: no cover

    def get_many(self, uris):
        """
        Return request uri map of found nodes as dicts:
            {requested_uri: {uri: x, content: y, meta: {}}}
        """
        raise NotImplementedError  # pragma: no cover

    def set(self, uri, content, **meta):
        """
        Persist node data and meta for uri.
        Return tuple of node dict and True if created and False if updated:
            {uri: x, content: y, meta: {}}, True|False
        """
        raise NotImplementedError  # pragma: no cover

    def delete(self, uri):
        """
        Delete node for uri and return node dict or None if not exists:
            {uri: x, content: y, meta: {}}
        """
        raise NotImplementedError  # pragma: no cover

    def delete_many(self, uris):
        """
        Delete node for uri and return request uri map of deleted nodes as dicts:
            {requested_uri: {uri: x, content: y, meta: {}}}
        """
        raise NotImplementedError  # pragma: no cover

    def publish(self, uri, **meta):
        """
        Return published node as dict or raise NodeDoesNotExist:
            {uri: x, content: y, meta: {}}
        """
        raise NotImplementedError  # pragma: no cover

    def get_revisions(self, uri):
        """
        Return list of tuples with uri and published state:
            [('i18n://sv-se@page/title.txt#1', False), ('i18n://sv-se@page/title.md#2', True)]
        """
        raise NotImplementedError  # pragma: no cover

    def search(self, uri):
        """
        Return list of non-versioned uri matches based on uri query pattern:
            ['i18n://sv-se@page/title.txt', ...]
        """
        raise NotImplementedError  # pragma: no cover


class DatabaseBackend(StorageBackend):

    def get(self, uri):
        node = self._get(uri)
        return self._serialize(uri, node)

    def get_many(self, uris):
        """
        Simple implementation,
        could be better implemented by backend not hitting db for every uri.
        """
        nodes = {}

        for uri in uris:
            try:
                node = self.get(uri)
            except NodeDoesNotExist:
                continue
            else:
                nodes[uri] = node

        return nodes

    def set(self, uri, content, **meta):
        """
        Dispatches private update/create handlers
        """
        try:
            node = self._update(uri, content, **meta)
            created = False
        except NodeDoesNotExist:
            node = self._create(uri, content, **meta)
            created = True
        return self._serialize(uri, node), created

    def delete(self, uri):
        node = None
        try:
            _node = self._get(uri)
        except NodeDoesNotExist:
            logger.warn('Tried to delete non existing node from storage: "%s"', uri)
        else:
            node = self._serialize(uri, _node)
            self._delete(_node)
        return node

    def delete_many(self, uris):
        """
        Simple implementation,
        could be better implemented by backend not hitting db for every uri.
        """
        deleted_nodes = {}

        for uri in uris:
            node = self.delete(uri)
            if node:
                deleted_nodes[uri] = node

        return deleted_nodes

    def _get(self, uri):
        raise NotImplementedError  # pragma: no cover

    def _create(self, uri, content, **meta):
        raise NotImplementedError  # pragma: no cover

    def _update(self, uri, content, **meta):
        raise NotImplementedError  # pragma: no cover

    def _delete(self, node):
        raise NotImplementedError  # pragma: no cover

    def _build_key(self, uri):
        """
        Build node identifying key for base uri.
        """
        return uri.clone(ext=None, version=None, query=None)

    def _serialize(self, uri, node):
        """
        Serialize node result as dict
        """
        meta = self._decode_meta(node['meta'], is_published=bool(node['is_published']))
        return {
            'uri': uri.clone(ext=node['plugin'], version=node['version']),
            'content': node['content'],
            'meta': meta
        }

    def _decode_meta(self, meta, **extra):
        """
        Decode and load underlying meta structure to dict and apply optional extra values.
        """
        _meta = json.loads(meta) if meta else {}
        _meta.update(extra)
        return _meta

    def _encode_meta(self, meta):
        """
        Encode meta dict for underlying persistence.
        """
        return json.dumps(meta) if meta else None

    def _merge_meta(self, encoded_meta, meta):
        """
        Merge new meta dict into encoded meta. Returns new encoded meta.
        """
        new_meta = None

        if meta:
            _meta = self._decode_meta(encoded_meta)
            for key, value in six.iteritems(meta):
                if value is None:
                    _meta.pop(key, None)
                else:
                    _meta[key] = value
            new_meta = self._encode_meta(_meta)

        return new_meta

    def _get_next_version(self, revisions):
        """
        Calculates new version number based on existing numeric ones.
        """
        versions = [0]
        for v in revisions:
            if v.isdigit():
                versions.append(int(v))
        return six.text_type(sorted(versions)[-1] + 1)
