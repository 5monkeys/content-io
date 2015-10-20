# coding=utf-8
from __future__ import unicode_literals

import six
import sqlite3
from sqlite3 import IntegrityError
from ..exceptions import NodeDoesNotExist, PersistenceError
from ...backends.base import DatabaseBackend
from ...conf.exceptions import ImproperlyConfigured
from ...utils.uri import URI


class SqliteBackend(DatabaseBackend):

    def __init__(self, **config):
        super(SqliteBackend, self).__init__(**config)
        self.debug = False
        self.queries = []
        if 'NAME' not in self.config:
            raise ImproperlyConfigured('Missing sqlite database name.')
        database = self.config['NAME']
        kwargs = self.config.get('OPTIONS', {})
        self._connection = sqlite3.connect(database, **kwargs)
        self._setup()

    def _setup(self):
        with self._connection as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS "content_io_node" (
                    "id" integer NOT NULL PRIMARY KEY ASC AUTOINCREMENT,
                    "key" varchar(255) NOT NULL,
                    "content" text NOT NULL,
                    "plugin" varchar(8) NOT NULL,
                    "version" varchar(255) NOT NULL,
                    "is_published" bool NOT NULL,
                    "meta" text
                );
            """)
            con.execute('CREATE INDEX IF NOT EXISTS "content_io_node_key" ON "content_io_node" ("key");')

    def start_debug(self):
        self.queries = []
        self.debug = True

    def stop_debug(self):
        self.queries = []
        self.debug = False

    def _call(self, command, query, **params):
        with self._connection as con:
            cursor = con.cursor()
            sql = command + ' ' + query
            cursor.execute(sql, params)
            if self.debug:
                self.queries.append({'sql': sql, 'params': params})
            return cursor

    def _call_select(self, query, **params):
        return self._call('SELECT', query, **params)

    def _call_insert(self, query, **params):
        self._call('INSERT INTO content_io_node', query, **params)

    def _call_update(self, query, **params):
        self._call('UPDATE content_io_node SET', query, **params)

    def _call_delete(self, where='', **params):
        command = 'DELETE FROM content_io_node'
        if where:
            command += ' WHERE'
        self._call(command, where, **params)

    def publish(self, uri, **meta):
        node = self._get(uri)

        if not node['is_published']:
            # Assign version number
            if not node['version'].isdigit():
                result = self._call_select('version FROM content_io_node WHERE key=:key', key=node['key'])
                revisions = (r[0] for r in result.fetchall())
                version = self._get_next_version(revisions)
                node['version'] = version

            # Un publish any other revision
            self._call_update('is_published=0 WHERE key=:key', key=node['key'])

            # Publish this version
            node['meta'] = self._merge_meta(node['meta'], meta)
            node['is_published'] = 1
            self._call_update('version=:version, is_published=1, meta=:meta WHERE id=:id',
                              id=node['id'],
                              version=node['version'],
                              meta=node['meta'])

        return self._serialize(uri, node)

    def get_revisions(self, uri):
        key = self._build_key(uri)
        nodes = self._call_select('plugin, version, is_published FROM content_io_node WHERE key=:key', key=key)
        return [(uri.clone(ext=ext, version=ver), bool(pub)) for ext, ver, pub in nodes.fetchall()]

    def search(self, uri):
        query = 'DISTINCT key, plugin FROM content_io_node'
        where = {}

        if uri.scheme:
            where['key LIKE :scheme'] = 'scheme', uri.scheme + '%'
        if uri.namespace:
            where['key LIKE :namespace'] = 'namespace', '%://' + uri.namespace + '@%'
        if uri.path:
            where['key LIKE :path'] = 'path', '%@' + uri.path + '%'

        if where:
            query += ' WHERE ' + ' AND '.join(where.keys())

        query += ' ORDER BY key, plugin'

        nodes = self._call_select(query, **dict(where.values()))
        return [URI(key).clone(ext=ext) for key, ext in nodes.fetchall()]

    def _get(self, uri):
        columns = ('id', 'key', 'content', 'plugin', 'version', 'is_published', 'meta')
        query = ', '.join(columns) + ' FROM content_io_node WHERE '
        statements = ['key=:key']
        params = {'key': self._build_key(uri)}

        if uri.ext:
            statements.append('plugin=:plugin')
            params['plugin'] = uri.ext
        if uri.version:
            statements.append('version=:version')
            params['version'] = uri.version
        else:
            statements.append('is_published=1')

        query += ' AND '.join(statements)
        result = self._call_select(query, **params)
        node = result.fetchone()

        if node is None:
            raise NodeDoesNotExist('Node for uri "%s" does not exist' % uri)
        else:
            return dict((c, v) for c, v in six.moves.zip(columns, node))

    def _create(self, uri, content, **meta):
        node = {
            'key': self._build_key(uri),
            'content': content,
            'plugin': uri.ext,
            'version': uri.version,
            'is_published': 0,
            'meta': self._encode_meta(meta)
        }
        try:
            self._call_insert("""
                              (key, content, plugin, version, is_published, meta) VALUES
                              (:key, :content, :plugin, :version, 0, :meta)
                              """, **node)
        except IntegrityError as e:
            raise PersistenceError('Failed to create node for uri "%s"; %s' % (uri, e))

        return node

    def _update(self, uri, content, **meta):
        node = self._get(uri)
        node.update({
            'content': content,
            'plugin': uri.ext,
            'version': uri.version,
            'meta': self._merge_meta(node['meta'], meta)
        })
        self._call_update("""
                          content=:content, plugin=:plugin, version=:version, meta=:meta
                          WHERE id=:id
                          """, **node)
        return node

    def _delete(self, node):
        self._call_delete('id=:id', id=node['id'])
