import pytest
import cio
from cio.backends import cache
from cio.pipeline import pipeline
from cio.backends import storage
from cio.backends.exceptions import NodeDoesNotExist
from cio.utils.uri import URI
from .asserts import assert_db, assert_cache


def test_get():
    node = cio.get('label/email', default=u'fallback')
    assert node.content == u'fallback'
    assert node.initial_uri == 'label/email'
    assert node.uri == 'i18n://sv-se@label/email.txt'


def test_get_with_empty_default():
    node = cio.get('page/title', default=u'', lazy=False)
    assert node.content == u''
    node = cio.get('page/body', default=None, lazy=False)
    assert node.content is None

    # Testing same non existing uri's twice to assert cache handles None/"" default
    node = cio.get('page/title', default=u'', lazy=False)
    assert node.content == u''
    node = cio.get('page/body', default=None, lazy=False)
    assert node.content is None


def test_set():
    with pytest.raises(URI.Invalid):
        cio.set('page/title', 'fail')

    with pytest.raises(URI.Invalid):
        cio.set('page/title.txt', 'fail')

    node = cio.set('i18n://sv-se@label/email.md', u'e-post')
    assert node.uri == 'i18n://sv-se@label/email.md#1'
    cache.clear()
    node = cio.get('label/email', u'fallback')
    assert node.content == u'<p>e-post</p>'
    assert node.uri == 'i18n://sv-se@label/email.md#1'
    assert node.initial == u'fallback'
    assert len(node.meta.keys()) == 0  # No meta returned from non-versioned api get
    assert repr(node._node) == '<Node: i18n://sv-se@label/email.md#1>'
    assert node.for_json() == {
        'uri': node.uri,
        'content': node.content,
        'meta': node.meta
    }

    node = cio.set('sv-se@label/email', u'e-post', publish=False)
    assert node.uri == 'i18n://sv-se@label/email.txt#draft'
    assert set(node.meta.keys()) == set(('modified_at', 'is_published'))

    node = cio.publish(node.uri)
    assert set(node.meta.keys()) == set(('modified_at', 'published_at', 'is_published'))
    assert node.meta['is_published'] is True

    node = cio.get('label/email')
    assert node.uri == 'i18n://sv-se@label/email.txt#2'
    assert node.content == u'e-post'
    assert node.uri.ext == 'txt'
    assert len(node.meta.keys()) == 0


def test_delete():
    with pytest.raises(URI.Invalid):
        cio.delete('foo/bar')

    node = cio.set('i18n://sv-se@label/email.txt', u'e-post')
    uri = node.uri
    assert cache.get(uri)['content'] == u'e-post'

    uris = cio.delete('sv-se@label/email#1', 'sv-se@foo/bar')
    assert uris == ['sv-se@label/email#1']

    with pytest.raises(NodeDoesNotExist):
        storage.get(uri)

    assert cache.get(uri) is None


def test_revisions():
    def assertRevisions(*revs):
        revisions = set(cio.revisions('i18n://sv-se@page/title'))
        assert revisions == set(revs)

    assert len(set(cio.revisions('i18n://sv-se@page/title'))) == 0

    # First draft
    with assert_db(selects=1, inserts=1, updates=0):
        with assert_cache(calls=0):
            node = cio.set('i18n://sv-se@page/title.txt', u'Djedi', publish=False)
            assert node.uri == 'i18n://sv-se@page/title.txt#draft'

    assertRevisions(('i18n://sv-se@page/title.txt#draft', False))
    assert cio.get('page/title').content is None

    # Publish first draft, version 1
    with assert_db(calls=4, selects=2, updates=2):
        with assert_cache(calls=1, sets=1):
            node = cio.publish(node.uri)
            assert node.uri == 'i18n://sv-se@page/title.txt#1'

    assertRevisions(('i18n://sv-se@page/title.txt#1', True))
    assert cio.get('page/title').content == u'Djedi'

    # Second draft
    with assert_db(selects=1, inserts=1, updates=0):
        with assert_cache(calls=0):
            node = cio.set('i18n://sv-se@page/title.md', u'# Djedi - Fast!', publish=False)
            assert node.uri == 'i18n://sv-se@page/title.md#draft'

    assertRevisions(('i18n://sv-se@page/title.txt#1', True), ('i18n://sv-se@page/title.md#draft', False))
    assert cio.get('page/title').content == u'Djedi'

    # Publish second draft, version 2
    with assert_db(calls=4, selects=2, updates=2):
        with assert_cache(calls=1, sets=1):
            node = cio.publish(node.uri)
            assert node.uri == 'i18n://sv-se@page/title.md#2'

    assertRevisions(('i18n://sv-se@page/title.txt#1', False), ('i18n://sv-se@page/title.md#2', True))
    assert cio.get('page/title').content == u'<h1>Djedi - Fast!</h1>'

    # Alter published version 2
    with assert_db(calls=2, selects=1, inserts=0, updates=1):
        with assert_cache(calls=0):
            node = cio.set('i18n://sv-se@page/title.md#2', u'# Djedi - Lightening fast!', publish=False)
            assert node.uri == 'i18n://sv-se@page/title.md#2'

    assertRevisions(('i18n://sv-se@page/title.txt#1', False), ('i18n://sv-se@page/title.md#2', True))
    assert cio.get('page/title').content == u'<h1>Djedi - Fast!</h1>'  # Not published, still in cache

    # Re-publish version 2, no change
    with assert_db(selects=1, inserts=0, updates=0):
        with assert_cache(calls=1, sets=1):
            node = cio.publish(node.uri)
            assert node.uri == 'i18n://sv-se@page/title.md#2'

    assertRevisions(('i18n://sv-se@page/title.txt#1', False), ('i18n://sv-se@page/title.md#2', True))
    assert cio.get('page/title').content == u'<h1>Djedi - Lightening fast!</h1>'

    # Rollback version 1
    with assert_db(calls=3, selects=1, updates=2):
        with assert_cache(calls=1, sets=1):
            node = cio.publish('i18n://sv-se@page/title#1')
            assert node.uri == 'i18n://sv-se@page/title.txt#1'

    assertRevisions(('i18n://sv-se@page/title.txt#1', True), ('i18n://sv-se@page/title.md#2', False))
    assert cio.get('page/title').content == u'Djedi'

    # Assert get specific version doesn't mess up the cache
    cache.clear()
    with assert_cache(calls=0):
        assert cio.get('page/title#2').content == u'<h1>Djedi - Lightening fast!</h1>'
    with assert_cache(calls=2, misses=1, sets=1):
        assert cio.get('page/title').content == u'Djedi'

    # Load version 1 and 2
    data = cio.load('sv-se@page/title#1')
    assert data['uri'] == 'i18n://sv-se@page/title.txt#1'
    assert data['data'] == u'Djedi'
    data = cio.load('sv-se@page/title#2')
    assert data['uri'] == 'i18n://sv-se@page/title.md#2'
    assert data['data'] == u'# Djedi - Lightening fast!'

    # Load without version and expect published version
    data = cio.load('sv-se@page/title')
    assert data['uri'] == 'i18n://sv-se@page/title.txt#1'
    assert data['data'] == u'Djedi'


def test_environment_state():
    with cio.env(i18n='en-us'):
        node = cio.get('page/title')
        assert node.uri == 'i18n://en-us@page/title.txt'

    node = cio.get('page/title')
    assert node.uri == 'i18n://sv-se@page/title.txt'


def test_non_distinct_uri():
    node1 = cio.get('page/title', u'Title1')
    node2 = cio.get('page/title', u'Title2')
    assert unicode(node1) == u'Title1'
    assert unicode(node2) == u'Title1'

    node1 = cio.get('page/title', u'Title1', lazy=False)
    cache.clear()
    node2 = cio.get('page/title', u'Title2', lazy=False)
    assert unicode(node1) == u'Title1'
    assert unicode(node2) == u'Title2'  # Second node not buffered, therefore unique default content


def test_fallback():
    with cio.env(i18n=('sv-se', 'en-us', 'en-uk')):
        node1 = cio.set('i18n://bogus@label/email.txt', u'epost')
        node2 = cio.set('i18n://en-uk@label/surname.txt', u'surname')

        with assert_cache(misses=2, sets=2):
            with assert_db(calls=6, selects=6):
                node3 = cio.get('i18n://label/email')
                node4 = cio.get('i18n://label/surname', u'efternamn')
                assert node3.content is None
                assert node4.content == u'surname'

        cache.clear()

        with assert_cache(misses=2, sets=2):
            with assert_db(calls=6):
                cio.get('i18n://label/email', lazy=False)
                cio.get('i18n://label/surname', u'lastname', lazy=False)


def test_uri_redirect():
    cio.set('i18n://sv-se@page/title.txt', u'Title')

    node = cio.get('i18n://sv-se@page/title', u'Default')
    assert node.uri == 'i18n://sv-se@page/title.txt#1'
    assert node.content == u'Title'

    node = cio.get('i18n://sv-se@page/title.md', u'# Default Markdown', lazy=False)
    assert node.uri == 'i18n://sv-se@page/title.md'
    assert node.content == u'<h1>Default Markdown</h1>'  # Cache still contains 'Title', but plugin diff and skipped
    cached_node = cache.get(node.uri)
    assert cached_node == {'uri': node.uri, 'content': u'<h1>Default Markdown</h1>'}

    cache.clear()
    node = cio.get('i18n://sv-se@page/title.md', u'Default Markdown', lazy=False)
    assert node.uri == 'i18n://sv-se@page/title.md'
    assert node.content == u'<p>Default Markdown</p>'  # Cache cleared, storage plugin mismatch, default fallback


def test_node_meta():
    node = cio.set('sv-se@page/title', u'', author=u'lundberg')
    assert node.meta.get('author') == u'lundberg'

    node = cio.get('page/title')
    assert len(node.meta.keys()) == 0  # Cached node has no meta

    node = cio.load('sv-se@page/title#1')
    assert set(node['meta'].keys()) == set(('author', 'modified_at', 'published_at', 'is_published'))
    assert node['meta'].get('author') == u'lundberg'

    cio.set('sv-se@page/title#1', u'', comment=u'This works!')
    node = cio.load('sv-se@page/title#1')
    assert set(node['meta'].keys()) == set(('author', 'comment', 'modified_at', 'published_at', 'is_published'))
    assert node['meta'].get('author') == u'lundberg'
    assert node['meta'].get('comment') == u'This works!'

    cio.set('sv-se@page/title#1', u'', comment=None)
    node = cio.load('sv-se@page/title#1')
    assert set(node['meta'].keys()) == set(('author', 'modified_at', 'published_at', 'is_published'))
    assert node['meta'].get('author') == u'lundberg'
    assert 'comment' not in node['meta']


def test_pipes_hits():
    with cio.env(i18n=('sv-se', 'en-us')):
        with assert_db(inserts=2):
            with assert_cache(calls=2, sets=2):
                cio.set('i18n://sv-se@label/email.txt', u'epost')
                cio.set('i18n://en-us@label/surname.txt', u'surname')

        # Lazy gets
        with assert_db(calls=0):
            with assert_cache(calls=0):
                node1 = cio.get('label/email')
                node2 = cio.get('i18n://label/surname')
                node3 = cio.get('i18n://monkey@label/zipcode', default=u'postnummer')

        # with assert_db(calls=2), assert_cache(calls=5, hits=1, misses=2, sets=2):
        with assert_db(calls=4, selects=4):
            with assert_cache(calls=2, hits=1, misses=2, sets=2):
                assert unicode(node1) == u'epost'
                assert node2.content == u'surname'
                assert unicode(node3) == u'postnummer'

        with assert_db(calls=0):
            with assert_cache(calls=1, hits=3):
                node1 = cio.get('label/email')
                node2 = cio.get('i18n://label/surname')
                node3 = cio.get('i18n://monkey@label/zipcode', default=u'postnummer')
                assert unicode(node1) == u'epost'
                assert node2.content == u'surname'
                assert unicode(node3) == u'postnummer'

                assert repr(node1) is not None
                assert str(node1) is not None


def test_forced_empty_content():
    with pytest.raises(ValueError):
        cio.set('i18n://sv-se@none', None)

    node = cio.set('i18n://sv-se@empty.txt', u'')
    node = cio.get(node.uri, default=u'fallback')
    assert unicode(node) == u''


def test_load_pipeline():
    with pytest.raises(ImportError):
        pipeline.add_pipe('foo.Bar')


def test_without_cache_pipe():
    # TODO: Test pipeline without CachePipe
    assert True
