import cio
from cio.backends import cache
from cio.pipeline import pipeline
from cio.backends import storage
from cio.backends.exceptions import NodeDoesNotExist
from cio.utils.uri import URI
from tests import BaseTest


class ApiTest(BaseTest):

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

    def test_set(self):
        with self.assertRaises(URI.Invalid):
            cio.set('page/title', 'fail')

        with self.assertRaises(URI.Invalid):
            cio.set('page/title.txt', 'fail')

        node = cio.set('i18n://sv-se@label/email.md', u'e-post')
        self.assertEqual(node.uri, 'i18n://sv-se@label/email.md#1')
        cache.clear()
        node = cio.get('label/email', u'fallback')
        self.assertEqual(node.content, u'<p>e-post</p>')
        self.assertEqual(node.uri, 'i18n://sv-se@label/email.md#1')
        self.assertEqual(node.initial, u'fallback')
        self.assertEqual(len(node.meta.keys()), 0)  # No meta returned from non-versioned api get
        self.assertEqual(repr(node._node), '<Node: i18n://sv-se@label/email.md#1>')
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
                node = cio.set('i18n://sv-se@page/title.md', u'# Content-IO - Fast!', publish=False)
                self.assertEqual(node.uri, 'i18n://sv-se@page/title.md#draft')

        assertRevisions(('i18n://sv-se@page/title.txt#1', True), ('i18n://sv-se@page/title.md#draft', False))
        self.assertEqual(cio.get('page/title').content, u'Content-IO')

        # Publish second draft, version 2
        with self.assertDB(calls=4, selects=2, updates=2):
            with self.assertCache(calls=1, sets=1):
                node = cio.publish(node.uri)
                self.assertEqual(node.uri, 'i18n://sv-se@page/title.md#2')

        assertRevisions(('i18n://sv-se@page/title.txt#1', False), ('i18n://sv-se@page/title.md#2', True))
        self.assertEqual(cio.get('page/title').content, u'<h1>Content-IO - Fast!</h1>')

        # Alter published version 2
        with self.assertDB(calls=2, selects=1, inserts=0, updates=1):
            with self.assertCache(calls=0):
                node = cio.set('i18n://sv-se@page/title.md#2', u'# Content-IO - Lightening fast!', publish=False)
                self.assertEqual(node.uri, 'i18n://sv-se@page/title.md#2')

        assertRevisions(('i18n://sv-se@page/title.txt#1', False), ('i18n://sv-se@page/title.md#2', True))
        self.assertEqual(cio.get('page/title').content, u'<h1>Content-IO - Fast!</h1>')  # Not published, still in cache

        # Re-publish version 2, no change
        with self.assertDB(selects=1, inserts=0, updates=0):
            with self.assertCache(calls=1, sets=1):
                node = cio.publish(node.uri)
                self.assertEqual(node.uri, 'i18n://sv-se@page/title.md#2')

        assertRevisions(('i18n://sv-se@page/title.txt#1', False), ('i18n://sv-se@page/title.md#2', True))
        self.assertEqual(cio.get('page/title').content, u'<h1>Content-IO - Lightening fast!</h1>')

        # Rollback version 1
        with self.assertDB(calls=3, selects=1, updates=2):
            with self.assertCache(calls=1, sets=1):
                node = cio.publish('i18n://sv-se@page/title#1')
                self.assertEqual(node.uri, 'i18n://sv-se@page/title.txt#1')

        assertRevisions(('i18n://sv-se@page/title.txt#1', True), ('i18n://sv-se@page/title.md#2', False))
        self.assertEqual(cio.get('page/title').content, u'Content-IO')

        # Assert get specific version doesn't mess up the cache
        cache.clear()
        with self.assertCache(calls=0):
            self.assertEqual(cio.get('page/title#2').content, u'<h1>Content-IO - Lightening fast!</h1>')
        with self.assertCache(calls=2, misses=1, sets=1):
            self.assertEqual(cio.get('page/title').content, u'Content-IO')

        # Load version 1 and 2
        data = cio.load('sv-se@page/title#1')
        self.assertEqual(data['uri'], 'i18n://sv-se@page/title.txt#1')
        self.assertEqual(data['data'], u'Content-IO')
        data = cio.load('sv-se@page/title#2')
        self.assertEqual(data['uri'], 'i18n://sv-se@page/title.md#2')
        self.assertEqual(data['data'], u'# Content-IO - Lightening fast!')

        # Load without version and expect published version
        data = cio.load('sv-se@page/title')
        self.assertEqual(data['uri'], 'i18n://sv-se@page/title.txt#1')
        self.assertEqual(data['data'], u'Content-IO')

    def test_environment_state(self):
        with cio.env(i18n='en-us'):
            node = cio.get('page/title')
            self.assertEqual(node.uri, 'i18n://en-us@page/title.txt')

        node = cio.get('page/title')
        self.assertEqual(node.uri, 'i18n://sv-se@page/title.txt')

    def test_non_distinct_uri(self):
        node1 = cio.get('page/title', u'Title1')
        node2 = cio.get('page/title', u'Title2')
        self.assertEqual(unicode(node1), u'Title1')
        self.assertEqual(unicode(node2), u'Title1')

        node1 = cio.get('page/title', u'Title1', lazy=False)
        cache.clear()
        node2 = cio.get('page/title', u'Title2', lazy=False)
        self.assertEqual(unicode(node1), u'Title1')
        self.assertEqual(unicode(node2), u'Title2')  # Second node not buffered, therefore unique default content

    def test_fallback(self):
        with cio.env(i18n=('sv-se', 'en-us', 'en-uk')):
            node1 = cio.set('i18n://bogus@label/email.txt', u'epost')
            node2 = cio.set('i18n://en-uk@label/surname.txt', u'surname')

            with self.assertCache(misses=2, sets=2):
                with self.assertDB(calls=6, selects=6):
                    node3 = cio.get('i18n://label/email')
                    node4 = cio.get('i18n://label/surname', u'efternamn')
                    self.assertIsNone(node3.content)
                    self.assertEqual(node4.content, u'surname')

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

        node = cio.get('i18n://sv-se@page/title.md', u'# Default Markdown', lazy=False)
        self.assertEqual(node.uri, 'i18n://sv-se@page/title.md')
        self.assertEqual(node.content, u'<h1>Default Markdown</h1>')  # Cache still contains 'Title', but plugin diff and skipped
        cached_node = cache.get(node.uri)
        self.assertDictEqual(cached_node, {'uri': node.uri, 'content': u'<h1>Default Markdown</h1>'})

        cache.clear()
        node = cio.get('i18n://sv-se@page/title.md', u'Default Markdown', lazy=False)
        self.assertEqual(node.uri, 'i18n://sv-se@page/title.md')
        self.assertEqual(node.content, u'<p>Default Markdown</p>')  # Cache cleared, storage plugin mismatch, default fallback

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
                    self.assertEqual(unicode(node1), u'epost')
                    self.assertEqual(node2.content, u'surname')
                    self.assertEqual(unicode(node3), u'postnummer')

            with self.assertDB(calls=0):
                with self.assertCache(calls=1, hits=3):
                    node1 = cio.get('label/email')
                    node2 = cio.get('i18n://label/surname')
                    node3 = cio.get('i18n://monkey@label/zipcode', default=u'postnummer')
                    self.assertEqual(unicode(node1), u'epost')
                    self.assertEqual(node2.content, u'surname')
                    self.assertEqual(unicode(node3), u'postnummer')

            self.assertIsNotNone(repr(node1))
            self.assertIsNotNone(str(node1))

    def test_forced_empty_content(self):
        with self.assertRaises(ValueError):
            cio.set('i18n://sv-se@none', None)

        node = cio.set('i18n://sv-se@empty.txt', u'')
        node = cio.get(node.uri, default=u'fallback')
        self.assertEqual(unicode(node), u'')

    def test_load_pipeline(self):
        with self.assertRaises(ImportError):
            pipeline.add_pipe('foo.Bar')
