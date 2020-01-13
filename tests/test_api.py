import cio
import six
import threading
from cio.backends import cache
from cio.conf import settings
from cio.conf.exceptions import ImproperlyConfigured
from cio.pipeline import pipeline
from cio.backends import storage
from cio.backends.exceptions import NodeDoesNotExist
from cio.utils.uri import URI
from tests import BaseTest


class ApiTest(BaseTest):

    def setUp(self):
        super(ApiTest, self).setUp()

        from cio.conf import settings
        settings.configure(
            PLUGINS=[
                'cio.plugins.txt.TextPlugin',
                'cio.plugins.md.MarkdownPlugin',
                'tests.UppercasePlugin'
            ]
        )

    def test_get(self):
        node = cio.get('label/email', default=u'fallback')
        self.assertEqual(node.content, u'fallback')
        self.assertEqual(node.initial_uri, 'label/email')
        self.assertEqual(node.uri, 'i18n://sv-se@label/email.txt')

    def test_get_with_empty_default(self):
        node = cio.get('page/title', default=u'', lazy=False)
        self.assertEqual(node.content, u'')
        node = cio.get('page/body', default=None, lazy=False)
        self.assertIsNone(node.content)

        # Testing same non existing uri's twice to assert cache handles None/"" default
        node = cio.get('page/title', default=u'', lazy=False)
        self.assertEqual(node.content, u'')
        node = cio.get('page/body', default=None, lazy=False)
        self.assertIsNone(node.content)

    def test_get_with_context(self):
        node = cio.get('page/title', default=u'{Welcome} {firstname} {lastname}!')
        content = node.render(firstname=u'Jonas', lastname=u'Lundberg')
        self.assertEqual(content, u'{Welcome} Jonas Lundberg!')

    def test_get_with_local_cache_pipe_settings(self):
        def assert_local_thread():
            settings.configure(local=True, CACHE={'PIPE': {'CACHE_ON_GET': False}})
            self.assertIn('BACKEND', settings.CACHE, 'Cache settings should be merged')

            # Test twice so that not the first get() caches the reponse in pipeline
            with self.assertCache(calls=1, misses=1, hits=0, sets=0):
                cio.get('local/settings', default=u'default', lazy=False)
            with self.assertCache(calls=1, misses=1, hits=0, sets=0):
                cio.get('local/settings', default=u'default', lazy=False)

        thread = threading.Thread(target=assert_local_thread)
        thread.start()
        thread.join()

        # Back on main thread, settings should not be affected
        # Test twice to make sure first get chaches the reponse in pipeline
        with self.assertCache(calls=2, misses=1, hits=0, sets=1):
            cio.get('local/settings', default=u'default', lazy=False)
        with self.assertCache(calls=1, misses=0, hits=1, sets=0):
            cio.get('local/settings', default=u'default', lazy=False)

    def test_set(self):
        with self.assertRaises(URI.Invalid):
            cio.set('page/title', 'fail')

        with self.assertRaises(URI.Invalid):
            cio.set('page/title.txt', 'fail')

        node = cio.set('i18n://sv-se@label/email.up', u'e-post')
        self.assertEqual(node.uri, 'i18n://sv-se@label/email.up#1')
        cache.clear()
        node = cio.get('label/email', u'fallback')
        self.assertEqual(node.content, u'E-POST')
        self.assertEqual(node.uri, 'i18n://sv-se@label/email.up#1')
        self.assertEqual(node.initial, u'fallback')
        self.assertEqual(len(node.meta.keys()), 0)  # No meta returned from non-versioned api get
        self.assertEqual(repr(node._node), '<Node: i18n://sv-se@label/email.up#1>')
        self.assertEqual(node.for_json(), {
            'uri': node.uri,
            'content': node.content,
            'meta': node.meta
        })

        node = cio.set('sv-se@label/email', u'e-post', publish=False)
        self.assertEqual(node.uri, 'i18n://sv-se@label/email.txt#draft')
        self.assertKeys(node.meta, 'modified_at', 'is_published')

        node = cio.publish(node.uri)
        self.assertKeys(node.meta, 'modified_at', 'published_at', 'is_published')
        self.assertTrue(node.meta['is_published'])

        node = cio.get('label/email')
        self.assertEqual(node.uri, 'i18n://sv-se@label/email.txt#2')
        self.assertEqual(node.content, u'e-post')
        self.assertEqual(node.uri.ext, 'txt')
        self.assertEqual(len(node.meta.keys()), 0)

        # Try publish non-existing node/uri
        node = cio.publish('i18n://sv-se@foo/bar.txt#draft')
        self.assertIsNone(node)

    def test_delete(self):
        with self.assertRaises(URI.Invalid):
            cio.delete('foo/bar')

        node = cio.set('i18n://sv-se@label/email.txt', u'e-post')
        uri = node.uri
        self.assertEqual(cache.get(uri)['content'], u'e-post')

        uris = cio.delete('sv-se@label/email#1', 'sv-se@foo/bar')
        self.assertListEqual(uris, ['sv-se@label/email#1'])

        with self.assertRaises(NodeDoesNotExist):
            storage.get(uri)

        self.assertIsNone(cache.get(uri))

    def test_revisions(self):
        def assertRevisions(*revs):
            revisions = set(cio.revisions('i18n://sv-se@page/title'))
            assert revisions == set(revs)

        self.assertEqual(len(set(cio.revisions('i18n://sv-se@page/title'))), 0)

        node = cio.load('sv-se@page/title')
        self.assertDictEqual(node, {
            'uri': 'i18n://sv-se@page/title.txt',
            'data': None,
            'content': None,
            'meta': {}
        })

        # First draft
        with self.assertDB(selects=1, inserts=1, updates=0):
            with self.assertCache(calls=0):
                node = cio.set('i18n://sv-se@page/title.txt', u'Content-IO', publish=False)
                self.assertEqual(node.uri, 'i18n://sv-se@page/title.txt#draft')

        assertRevisions(('i18n://sv-se@page/title.txt#draft', False))
        self.assertIsNone(cio.get('page/title').content)

        # Publish first draft, version 1
        with self.assertDB(calls=4, selects=2, updates=2):
            with self.assertCache(calls=1, sets=1):
                node = cio.publish(node.uri)
                self.assertEqual(node.uri, 'i18n://sv-se@page/title.txt#1')

        assertRevisions(('i18n://sv-se@page/title.txt#1', True))
        self.assertEqual(cio.get('page/title').content, u'Content-IO')

        # Second draft
        with self.assertDB(selects=1, inserts=1, updates=0):
            with self.assertCache(calls=0):
                node = cio.set('i18n://sv-se@page/title.up', u'Content-IO - Fast!', publish=False)
                self.assertEqual(node.uri, 'i18n://sv-se@page/title.up#draft')

        assertRevisions(('i18n://sv-se@page/title.txt#1', True), ('i18n://sv-se@page/title.up#draft', False))
        self.assertEqual(cio.get('page/title').content, u'Content-IO')

        # Publish second draft, version 2
        with self.assertDB(calls=4, selects=2, updates=2):
            with self.assertCache(calls=1, sets=1):
                node = cio.publish(node.uri)
                self.assertEqual(node.uri, 'i18n://sv-se@page/title.up#2')

        assertRevisions(('i18n://sv-se@page/title.txt#1', False), ('i18n://sv-se@page/title.up#2', True))
        self.assertEqual(cio.get('page/title').content, u'CONTENT-IO - FAST!')

        # Alter published version 2
        with self.assertDB(calls=2, selects=1, inserts=0, updates=1):
            with self.assertCache(calls=0):
                node = cio.set('i18n://sv-se@page/title.up#2', u'Content-IO - Lightening fast!', publish=False)
                self.assertEqual(node.uri, 'i18n://sv-se@page/title.up#2')

        assertRevisions(('i18n://sv-se@page/title.txt#1', False), ('i18n://sv-se@page/title.up#2', True))
        self.assertEqual(cio.get('page/title').content, u'CONTENT-IO - FAST!')  # Not published, still in cache

        # Re-publish version 2, no change
        with self.assertDB(selects=1, inserts=0, updates=0):
            with self.assertCache(calls=1, sets=1):
                node = cio.publish(node.uri)
                self.assertEqual(node.uri, 'i18n://sv-se@page/title.up#2')

        assertRevisions(('i18n://sv-se@page/title.txt#1', False), ('i18n://sv-se@page/title.up#2', True))
        self.assertEqual(cio.get('page/title').content, u'CONTENT-IO - LIGHTENING FAST!')

        # Rollback version 1
        with self.assertDB(calls=3, selects=1, updates=2):
            with self.assertCache(calls=1, sets=1):
                node = cio.publish('i18n://sv-se@page/title#1')
                self.assertEqual(node.uri, 'i18n://sv-se@page/title.txt#1')

        assertRevisions(('i18n://sv-se@page/title.txt#1', True), ('i18n://sv-se@page/title.up#2', False))
        self.assertEqual(cio.get('page/title').content, u'Content-IO')

        # Assert get specific version doesn't mess up the cache
        cache.clear()
        with self.assertCache(calls=0):
            self.assertEqual(cio.get('page/title#2').content, u'CONTENT-IO - LIGHTENING FAST!')
        with self.assertCache(calls=2, misses=1, sets=1):
            self.assertEqual(cio.get('page/title').content, u'Content-IO')

        # Load version 1 and 2
        data = cio.load('sv-se@page/title#1')
        self.assertEqual(data['uri'], 'i18n://sv-se@page/title.txt#1')
        self.assertEqual(data['data'], u'Content-IO')
        data = cio.load('sv-se@page/title#2')
        self.assertEqual(data['uri'], 'i18n://sv-se@page/title.up#2')
        self.assertEqual(data['data'], {u'name': u'Content-IO - Lightening fast!'})

        # Load without version and expect published version
        data = cio.load('sv-se@page/title')
        self.assertEqual(data['uri'], 'i18n://sv-se@page/title.txt#1')
        self.assertEqual(data['data'], u'Content-IO')

    def test_search(self):
        cio.set('i18n://sv-se@label/email.txt', u'e-post')
        uris = cio.search()
        self.assertEqual(len(uris), 1)
        uris = cio.search('foo/')
        self.assertEqual(len(uris), 0)
        uris = cio.search('label/')
        self.assertEqual(len(uris), 1)

    def test_environment_state(self):
        with cio.env(i18n='en-us'):
            node = cio.get('page/title')
            self.assertEqual(node.uri, 'i18n://en-us@page/title.txt')

        node = cio.get('page/title')
        self.assertEqual(node.uri, 'i18n://sv-se@page/title.txt')

    def test_non_distinct_uri(self):
        node1 = cio.get('page/title', u'Title1')
        node2 = cio.get('page/title', u'Title2')
        self.assertEqual(six.text_type(node1), u'Title1')
        self.assertEqual(six.text_type(node2), u'Title1')

        node1 = cio.get('page/title', u'Title1', lazy=False)
        cache.clear()
        node2 = cio.get('page/title', u'Title2', lazy=False)
        self.assertEqual(six.text_type(node1), u'Title1')
        self.assertEqual(six.text_type(node2), u'Title2')  # Second node not buffered, therefore unique default content

    def test_fallback(self):
        with cio.env(i18n=('sv-se', 'en-us', 'en-uk')):
            cio.set('i18n://bogus@label/email.txt', u'epost')
            cio.set('i18n://en-uk@label/surname.txt', u'surname')

            with self.assertCache(misses=2, sets=2):
                with self.assertDB(calls=6, selects=6):
                    node1 = cio.get('i18n://label/email')
                    node2 = cio.get('i18n://label/surname', u'efternamn')
                    self.assertEqual(node1.uri.namespace, 'sv-se')  # No fallback, stuck on first namespace, sv-se
                    self.assertEqual(node1.namespace_uri.namespace, 'sv-se')
                    self.assertIsNone(node1.content)
                    self.assertEqual(node2.uri.namespace, 'en-uk')
                    self.assertEqual(node2.namespace_uri.namespace, 'sv-se')
                    self.assertEqual(node2.content, u'surname')

            cache.clear()

            with self.assertCache(misses=2, sets=2):
                with self.assertDB(calls=6):
                    cio.get('i18n://label/email', lazy=False)
                    cio.get('i18n://label/surname', u'lastname', lazy=False)

    def test_uri_redirect(self):
        cio.set('i18n://sv-se@page/title.txt', u'Title')

        node = cio.get('i18n://sv-se@page/title', u'Default')
        self.assertEqual(node.uri, 'i18n://sv-se@page/title.txt#1')
        self.assertEqual(node.content, u'Title')

        node = cio.get('i18n://sv-se@page/title.up', u'Default Upper', lazy=False)
        self.assertEqual(node.uri, 'i18n://sv-se@page/title.up')
        self.assertEqual(node.content, u'DEFAULT UPPER')  # Cache still contains 'Title', but plugin diff and skipped
        cached_node = cache.get(node.uri)
        self.assertDictEqual(cached_node, {'uri': node.uri, 'content': u'DEFAULT UPPER'})

        cache.clear()
        node = cio.get('i18n://sv-se@page/title.up', u'Default-Upper', lazy=False)
        self.assertEqual(node.uri, 'i18n://sv-se@page/title.up')
        self.assertEqual(node.content, u'DEFAULT-UPPER')  # Cache cleared, storage plugin mismatch, default fallback

    def test_node_meta(self):
        node = cio.set('sv-se@page/title', u'', author=u'lundberg')
        self.assertEqual(node.meta.get('author'), u'lundberg')

        node = cio.get('page/title')
        self.assertEqual(len(node.meta.keys()), 0)  # Cached node has no meta

        node = cio.load('sv-se@page/title#1')
        meta = node['meta']
        self.assertKeys(meta, 'author', 'modified_at', 'published_at', 'is_published')
        self.assertEqual(meta.get('author'), u'lundberg')

        cio.set('sv-se@page/title#1', u'', comment=u'This works!')
        node = cio.load('sv-se@page/title#1')
        meta = node['meta']
        self.assertKeys(meta, 'author', 'comment', 'modified_at', 'published_at', 'is_published')
        self.assertEqual(meta.get('author'), u'lundberg')
        self.assertEqual(meta.get('comment'), u'This works!')

        cio.set('sv-se@page/title#1', u'', comment=None)
        node = cio.load('sv-se@page/title#1')
        meta = node['meta']
        self.assertKeys(meta, 'author', 'modified_at', 'published_at', 'is_published')
        self.assertEqual(meta.get('author'), u'lundberg')
        self.assertNotIn('comment', meta)

    def test_pipes_hits(self):
        with cio.env(i18n=('sv-se', 'en-us')):
            with self.assertDB(inserts=2):
                with self.assertCache(calls=2, sets=2):
                    cio.set('i18n://sv-se@label/email.txt', u'epost')
                    cio.set('i18n://en-us@label/surname.txt', u'surname')

            # Lazy gets
            with self.assertDB(calls=0):
                with self.assertCache(calls=0):
                    node1 = cio.get('label/email')
                    node2 = cio.get('i18n://label/surname')
                    node3 = cio.get('i18n://monkey@label/zipcode', default=u'postnummer')

            # with self.assertDB(calls=2), self.assertCache(calls=5, hits=1, misses=2, sets=2):
            with self.assertDB(calls=4, selects=4):
                with self.assertCache(calls=2, hits=1, misses=2, sets=2):
                    self.assertEqual(six.text_type(node1), u'epost')
                    self.assertEqual(node2.content, u'surname')
                    self.assertEqual(six.text_type(node3), u'postnummer')

            with self.assertDB(calls=0):
                with self.assertCache(calls=1, hits=3):
                    node1 = cio.get('label/email')
                    node2 = cio.get('i18n://label/surname')
                    node3 = cio.get('i18n://monkey@label/zipcode', default=u'postnummer')
                    self.assertEqual(six.text_type(node1), u'epost')
                    self.assertEqual(node2.content, u'surname')
                    self.assertEqual(six.text_type(node3), u'postnummer')

            self.assertIsNotNone(repr(node1))
            self.assertIsNotNone(str(node1))

    def test_forced_empty_content(self):
        with self.assertRaises(ValueError):
            cio.set('i18n://sv-se@none', None)

        node = cio.set('i18n://sv-se@empty.txt', u'')
        node = cio.get(node.uri, default=u'fallback')
        self.assertEqual(six.text_type(node), u'')

    def test_load_pipeline(self):
        with self.assertRaises(ImportError):
            pipeline.add_pipe('foo.Bar')

    def test_unknown_plugin(self):
        with self.assertRaises(ImproperlyConfigured):
            cio.set('i18n://sv-se@foo/bar.baz#draft', 'raise')

    def test_abandoned_buffered_node(self):
        cio.set('sv-se@foo/bar', u'foobar')

        node = cio.get('foo/bar')
        self.assertFalse(node._flushed)
        self.assertIn('get', pipeline._buffer._buffer)

        # Mess things up...
        pipeline.clear()
        self.assertFalse(node._flushed)
        self.assertNotIn('get', pipeline._buffer._buffer)

        self.assertEqual(node.content, u'foobar')
        self.assertTrue(node._flushed)

    def test_publish_without_version(self):
        cio.set('i18n://sv-se@page/apa.txt', u'Bananas', publish=False)
        node = cio.publish('i18n://sv-se@page/apa.txt')
        self.assertEqual(node.content, 'Bananas')

    def test_load_without_version(self):
        cio.set('i18n://sv-se@page/apa.txt', u'Many bananas')
        node = cio.load('i18n://sv-se@page/apa.txt')
        self.assertEqual(node['content'], 'Many bananas')

    def test_load_new_without_extension(self):
        node = cio.load('i18n://sv-se@page/monkey')
        self.assertEqual(node['content'], None)
