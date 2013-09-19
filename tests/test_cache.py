import pytest
import cio
from cio.backends import cache, storage
from cio.backends.exceptions import NodeDoesNotExist
from cio.utils.uri import URI
from .asserts import assert_cache

uri = 'i18n://sv-se@label/email.txt'


def test_cached_node():
    with pytest.raises(NodeDoesNotExist):
        storage.get(uri)

    content = cache.get(uri)
    assert content is None

    node, _ = storage.set(uri + '#draft', u'e-post')
    storage.publish(node['uri'])

    with assert_cache(calls=2, misses=1, sets=1):
        node = cio.get('i18n://label/email', lazy=False)

    cached_node = cache.get('i18n://sv-se@label/email')
    assert isinstance(cached_node, dict)
    assert set(cached_node.keys()) == set(('uri', 'content'))
    _uri, content = cached_node['uri'], cached_node['content']
    assert _uri == 'i18n://sv-se@label/email.txt#1'
    assert content == node.content == u'e-post'

    with assert_cache(calls=1, misses=0, hits=1):
        node = cio.get('i18n://label/email', lazy=False)
        assert node.uri == 'i18n://sv-se@label/email.txt#1'

    cio.delete(uri)
    content = cache.get(uri)
    assert content is None


def test_cache_encoding():
    cio.set(uri, u'epost')

    cached_node = cache.get(uri)
    content = cached_node['content']
    assert isinstance(content, unicode)
    assert content == u'epost'

    cache.set('i18n://sv-se@label/email.txt#1', u'epost')
    nodes = cache.get_many((uri, uri))
    assert nodes == {uri: {'uri': 'i18n://sv-se@label/email.txt#1', 'content': u'epost'}}


def test_cache_delete():
    uris = ['i18n://sv-se@foo.txt', 'i18n://sv-se@bar.txt']

    cache.set(uris[0], u'Foo')
    cache.set(uris[1], u'Bar')

    with assert_cache(hits=2):
        cache.get_many(uris)

    cache.delete_many(uris)

    with assert_cache(misses=2):
        cache.get_many(uris)


def test_cache_set():
    with pytest.raises(URI.Invalid):
        cache.set('i18n://sv-se@foo', u'Bar')

    nodes = {
        'i18n://sv-se@foo.txt#1': u'Foo',
        'i18n://sv-se@bar.txt#2': u'Bar'
    }
    cache.set_many(nodes)

    with assert_cache(calls=1, hits=2):
        result = cache.get_many(['i18n://sv-se@foo', 'i18n://sv-se@bar'])
        assert result == {
            'i18n://sv-se@foo': {'uri': 'i18n://sv-se@foo.txt#1', 'content': u'Foo'},
            'i18n://sv-se@bar': {'uri': 'i18n://sv-se@bar.txt#2', 'content': u'Bar'}
        }
