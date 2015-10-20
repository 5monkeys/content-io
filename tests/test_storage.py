from cio.backends import get_backend, storage
from cio.backends.base import CacheBackend, StorageBackend, DatabaseBackend
from cio.backends.exceptions import InvalidBackend, PersistenceError, NodeDoesNotExist
from cio.backends.sqlite import SqliteBackend
from cio.conf.exceptions import ImproperlyConfigured
from cio.utils.uri import URI
from tests import BaseTest


class StorageTest(BaseTest):

    def test_get_storage(self):
        backend = get_backend('sqlite://:memory:')
        self.assertTrue(issubclass(backend.__class__, StorageBackend))

        backend = '.'.join((SqliteBackend.__module__, SqliteBackend.__name__))
        with self.assertRaises(ImproperlyConfigured):
            backend = get_backend(backend)

        backend = get_backend({
            'BACKEND': backend,
            'NAME': ':memory:'
        })
        self.assertTrue(issubclass(backend.__class__, DatabaseBackend))

        with self.assertRaises(ImportError):
            get_backend('foo.Bar')
        with self.assertRaises(ImportError):
            get_backend('cio.storage.backends.orm.Bogus')
        with self.assertRaises(InvalidBackend):
            get_backend('invalid')
        with self.assertRaises(InvalidBackend):
            get_backend('foo://')

    def test_bogus_backend(self):
        class BogusStorage(CacheBackend, StorageBackend):
            pass
        bogus = BogusStorage()
        self.assertIsNone(bogus.scheme)
        with self.assertRaises(NotImplementedError):
            bogus._get(None)
        with self.assertRaises(NotImplementedError):
            bogus._get_many(None)
        with self.assertRaises(NotImplementedError):
            bogus._set(None, None)
        with self.assertRaises(NotImplementedError):
            bogus._set_many(None)
        with self.assertRaises(NotImplementedError):
            bogus._delete(None)
        with self.assertRaises(NotImplementedError):
            bogus._delete_many(None)
        with self.assertRaises(NotImplementedError):
            bogus.publish(None)
        with self.assertRaises(NotImplementedError):
            bogus.get_revisions(None)

    def test_create_update(self):
        storage.set('i18n://sv-se@a.txt#draft', u'first')
        node = storage.get('i18n://sv-se@a#draft')
        self.assertEqual(node['content'], u'first')
        self.assertEqual(node['uri'], 'i18n://sv-se@a.txt#draft')
        storage.set('i18n://sv-se@a.txt#draft', u'second')
        node = storage.get('i18n://sv-se@a#draft')
        self.assertEqual(node['content'], u'second')
        self.assertEqual(node['uri'], 'i18n://sv-se@a.txt#draft')

    def test_get(self):
        storage.set('i18n://sv-se@a.txt#draft', u'A')
        storage.set('i18n://sv-se@b.md#draft', u'B')
        node = storage.get('i18n://sv-se@a#draft')
        self.assertEqual(node['uri'], 'i18n://sv-se@a.txt#draft')
        self.assertEqual(node['content'], u'A')

        storage.publish('i18n://sv-se@a#draft')
        storage.publish('i18n://sv-se@b#draft')

        nodes = storage.get_many(('i18n://sv-se@a', 'i18n://sv-se@b'))
        for node in nodes.values():
            node.pop('meta')
        self.assertDictEqual(nodes, {
            'i18n://sv-se@a': {
                'uri': 'i18n://sv-se@a.txt#1',
                'content': u'A'
            },
            'i18n://sv-se@b': {
                'uri': 'i18n://sv-se@b.md#1',
                'content': u'B'
            }
        })

    def test_delete(self):
        storage.set('i18n://sv-se@a.txt#draft', u'A')
        storage.set('i18n://sv-se@b.txt#draft', u'B')

        node = storage.get('i18n://sv-se@a#draft')
        self.assertEqual(node['content'], u'A')

        deleted_node = storage.delete('sv-se@a#draft')
        deleted_node.pop('meta')
        self.assertDictEqual(deleted_node, {'uri': 'i18n://sv-se@a.txt#draft', 'content': u'A'})

        deleted_nodes = storage.delete_many(('sv-se@a#draft', 'sv-se@b#draft'))
        for node in deleted_nodes.values():
            node.pop('meta')
        self.assertDictEqual(deleted_nodes, {
            'i18n://sv-se@b#draft': {'uri': 'i18n://sv-se@b.txt#draft', 'content': u'B'}
        })

    def test_nonexisting_node(self):
        with self.assertRaises(URI.Invalid):
            storage.get('?')
        with self.assertRaises(NodeDoesNotExist):
            storage.get('sv-se@page/title')

    def test_plugin_mismatch(self):
        storage.set('i18n://sv-se@a.txt#draft', u'A')
        storage.publish('i18n://sv-se@a.txt#draft')

        with self.assertRaises(NodeDoesNotExist):
            storage.get('i18n://sv-se@a.md')

        nodes = storage.get_many(('i18n://sv-se@a.md',))
        self.assertDictEqual(nodes, {})

    def test_node_integrity(self):
        storage.backend._create(URI('i18n://sv-se@a.txt#draft'), u'first')
        with self.assertRaises(PersistenceError):
            storage.backend._create(URI('i18n://sv-se@a'), u'second')
        with self.assertRaises(PersistenceError):
            storage.backend._create(URI('i18n://sv-se@a.txt'), u'second')
        with self.assertRaises(PersistenceError):
            storage.backend._create(URI('i18n://sv-se@a#draft'), u'second')

    def test_search(self):
        storage.set('i18n://sv-se@foo/bar.txt#draft', u'')
        storage.set('i18n://sv-se@foo/bar/baz.md#draft', u'')
        storage.set('i18n://en@foo/bar/baz.md#draft', u'')
        storage.set('i18n://en@foo/bar/baz.md#1', u'')
        storage.set('i18n://en@ham/spam.txt#draft', u'')
        storage.set('l10n://a@foo/bar.md#draft', u'')
        storage.set('l10n://b@foo/bar/baz.txt#draft', u'')

        uris = storage.search()
        self.assertListEqual(uris, [
            'i18n://en@foo/bar/baz.md',
            'i18n://en@ham/spam.txt',
            'i18n://sv-se@foo/bar.txt',
            'i18n://sv-se@foo/bar/baz.md',
            'l10n://a@foo/bar.md',
            'l10n://b@foo/bar/baz.txt',
        ])

        uris = storage.search('i18n://')
        self.assertListEqual(uris, [
            'i18n://en@foo/bar/baz.md',
            'i18n://en@ham/spam.txt',
            'i18n://sv-se@foo/bar.txt',
            'i18n://sv-se@foo/bar/baz.md',
        ])

        uris = storage.search('en@')
        self.assertListEqual(uris, [
            'i18n://en@foo/bar/baz.md',
            'i18n://en@ham/spam.txt',
        ])

        uris = storage.search('foo/')
        self.assertListEqual(uris, [
            'i18n://en@foo/bar/baz.md',
            'i18n://sv-se@foo/bar.txt',
            'i18n://sv-se@foo/bar/baz.md',
            'l10n://a@foo/bar.md',
            'l10n://b@foo/bar/baz.txt',
        ])

        uris = storage.search('sv-se@foo/')
        self.assertListEqual(uris, [
            'i18n://sv-se@foo/bar.txt',
            'i18n://sv-se@foo/bar/baz.md',
        ])

        uris = storage.search('i18n://foo/')
        self.assertListEqual(uris, [
            'i18n://en@foo/bar/baz.md',
            'i18n://sv-se@foo/bar.txt',
            'i18n://sv-se@foo/bar/baz.md',
        ])

        uris = storage.search('i18n://en@')
        self.assertListEqual(uris, [
            'i18n://en@foo/bar/baz.md',
            'i18n://en@ham/spam.txt',
        ])
