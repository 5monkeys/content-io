import cio
import six
from cio.backends import cache, storage
from cio.backends.exceptions import NodeDoesNotExist
from cio.utils.uri import URI
from tests import BaseTest


class CacheTest(BaseTest):

    uri = 'i18n://sv-se@label/email.txt'

    def test_cached_node(self):
        with self.assertRaises(NodeDoesNotExist):
            storage.get(self.uri)

        content = cache.get(self.uri)
        self.assertIsNone(content)

        node, _ = storage.set(self.uri + '#draft', u'e-post')
        storage.publish(node['uri'])

        with self.assertCache(calls=2, misses=1, sets=1):
            node = cio.get('i18n://label/email', lazy=False)

        cached_node = cache.get('i18n://sv-se@label/email')
        self.assertIsInstance(cached_node, dict)
        self.assertKeys(cached_node, 'uri', 'content')
        _uri, content = cached_node['uri'], cached_node['content']
        self.assertEqual(_uri, 'i18n://sv-se@label/email.txt#1')
        self.assertTrue(content == node.content == u'e-post')

        with self.assertCache(calls=1, misses=0, hits=1):
            node = cio.get('i18n://label/email', lazy=False)
            self.assertEqual(node.uri, 'i18n://sv-se@label/email.txt#1')

        cio.delete(self.uri)
        content = cache.get(self.uri)
        self.assertIsNone(content)

    def test_cache_encoding(self):
        cio.set(self.uri, u'epost')

        cached_node = cache.get(self.uri)
        content = cached_node['content']
        self.assertIsInstance(content, six.text_type)
        self.assertEqual(content, u'epost')

        cache.set('i18n://sv-se@label/email.txt#1', u'epost')
        nodes = cache.get_many((self.uri, self.uri))
        self.assertDictEqual(nodes, {self.uri: {'uri': 'i18n://sv-se@label/email.txt#1', 'content': u'epost'}})

    def test_cache_delete(self):
        uris = ['i18n://sv-se@foo.txt', 'i18n://sv-se@bar.txt']

        cache.set(uris[0], u'Foo')
        cache.set(uris[1], u'Bar')

        with self.assertCache(hits=2):
            cache.get_many(uris)

        cache.delete_many(uris)

        with self.assertCache(misses=2):
            cache.get_many(uris)

    def test_cache_set(self):
        with self.assertRaises(URI.Invalid):
            cache.set('i18n://sv-se@foo', u'Bar')

        nodes = {
            'i18n://sv-se@foo.txt#1': u'Foo',
            'i18n://sv-se@bar.txt#2': u'Bar'
        }
        cache.set_many(nodes)

        with self.assertCache(calls=1, hits=2):
            result = cache.get_many(['i18n://sv-se@foo', 'i18n://sv-se@bar'])
            self.assertDictEqual(result, {
                'i18n://sv-se@foo': {'uri': 'i18n://sv-se@foo.txt#1', 'content': u'Foo'},
                'i18n://sv-se@bar': {'uri': 'i18n://sv-se@bar.txt#2', 'content': u'Bar'}
            })
