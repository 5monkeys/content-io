from collections import defaultdict
from cio.backends.base import StorageBackend
from cio.backends.exceptions import NodeDoesNotExist


class LocMemStorageBackend(StorageBackend):

    def __init__(self):
        self._db = defaultdict(list)

    def _key(self, uri):
        return uri.clone(ext=None, version=None)

    def _list(self, uri):
        return self._db[self._key(uri)]

    def _obj(self, node):
        o = dict((key, value) for key, value in node.iteritems() if key in ('uri', 'content', 'meta'))
        assert 'is_published' in o['meta']
        return o

    def _get(self, uri):
        nodes = self._list(uri)

        if nodes:
            if uri.ext:
                nodes = filter(lambda n: n['uri'].ext == uri.ext, nodes)
            if uri.version:
                nodes = filter(lambda n: n['uri'].version == uri.version, nodes)
            else:
                nodes = filter(lambda n: n['meta'].get('is_published', False), nodes)

        if nodes:
            return nodes[-1]
        else:
            raise NodeDoesNotExist(uri)

    def get(self, uri):
        return self._obj(self._get(uri))

    def get_many(self, uris):
        nodes = {}
        for uri in uris:
            try:
                node = self._get(uri)
                nodes[uri] = self._obj(node)
            except NodeDoesNotExist:
                pass
        return nodes

    def set(self, uri, content, **meta):
        try:
            node = self._get(uri)
            node['content'] = content
            node['meta'].update(meta)
            created = False
        except NodeDoesNotExist:
            key = self._key(uri)
            meta['is_published'] = False
            node = {
                'uri': uri,
                'content': content,
                'meta': meta
            }
            self._db[key].append(node)
            created = True
        finally:
            return self._obj(node), created

    def delete(self, uri):
        deleted_nodes = self.delete_many((uri,))
        return deleted_nodes.get(uri)

    def delete_many(self, uris):
        deleted_nodes = {}
        for uri in uris:
            nodes = []
            for node in self._list(uri):
                if (not uri.ext or uri.ext == node['uri'].ext) and \
                        (not uri.version or uri.version == node['uri'].version):
                    deleted_nodes[uri] = self._obj(node)
                else:
                    nodes.append(node)
            # nodes = []
            # for node in self._list(uri):
            #     if node['uri'] == uri:
            #         deleted_nodes[uri] = self._obj(node)
            #     else:
            #         nodes.append(node)
            key = self._key(uri)
            self._db[key] = nodes
        return deleted_nodes

    def publish(self, uri, **meta):
        node = self._get(uri)
        for n in self._list(uri):
            n['meta']['is_published'] = False
        versions = [uri.version for uri, _ in self.get_revisions(uri)]
        version = self._get_next_version(versions)
        node['uri'] = node['uri'].clone(version=version)
        node['meta'].update(meta)
        node['meta']['is_published'] = True
        return self._obj(node)

    def get_revisions(self, uri):
        return [(node['uri'], node['meta']['is_published']) for node in self._list(uri)]
