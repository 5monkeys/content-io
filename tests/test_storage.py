import pytest
from cio.backends import get_backend, storage
from cio.backends.base import CacheBackend, StorageBackend, DatabaseBackend
from cio.backends.exceptions import InvalidBackend, PersistenceError, NodeDoesNotExist
from cio.backends.sqlite import SqliteBackend
from cio.conf.exceptions import ImproperlyConfigured
from cio.utils.uri import URI


def test_get_storage():
    backend = get_backend('sqlite://:memory:')
    assert issubclass(backend.__class__, StorageBackend)

    backend = '.'.join((SqliteBackend.__module__, SqliteBackend.__name__))
    with pytest.raises(ImproperlyConfigured):
        backend = get_backend(backend)

    backend = get_backend({
        'BACKEND': backend,
        'NAME': ':memory:'
    })
    assert issubclass(backend.__class__, DatabaseBackend)

    with pytest.raises(ImportError):
        get_backend('foo.Bar')
    with pytest.raises(ImportError):
        get_backend('cio.storage.backends.orm.Bogus')
    with pytest.raises(InvalidBackend):
        get_backend('invalid')
    with pytest.raises(InvalidBackend):
        get_backend('foo://')


def test_bogus_backend():
    class BogusStorage(CacheBackend, StorageBackend):
        pass
    bogus = BogusStorage()
    assert bogus.scheme is None
    with pytest.raises(NotImplementedError):
        bogus._get(None)
    with pytest.raises(NotImplementedError):
        bogus._get_many(None)
    with pytest.raises(NotImplementedError):
        bogus._set(None, None)
    with pytest.raises(NotImplementedError):
        bogus._set_many(None)
    with pytest.raises(NotImplementedError):
        bogus._delete(None)
    with pytest.raises(NotImplementedError):
        bogus._delete_many(None)
    with pytest.raises(NotImplementedError):
        bogus.publish(None)
    with pytest.raises(NotImplementedError):
        bogus.get_revisions(None)


def test_create_update():
    storage.set('i18n://sv-se@a.txt#draft', u'first')
    node = storage.get('i18n://sv-se@a#draft')
    assert node['content'] == u'first'
    assert node['uri'] == 'i18n://sv-se@a.txt#draft'
    storage.set('i18n://sv-se@a.txt#draft', u'second')
    node = storage.get('i18n://sv-se@a#draft')
    assert node['content'] == u'second'
    assert node['uri'] == 'i18n://sv-se@a.txt#draft'


def test_get():
    storage.set('i18n://sv-se@a.txt#draft', u'A')
    storage.set('i18n://sv-se@b.md#draft', u'B')
    node = storage.get('i18n://sv-se@a#draft')
    assert node['uri'] == 'i18n://sv-se@a.txt#draft'
    assert node['content'] == u'A'

    storage.publish('i18n://sv-se@a#draft')
    storage.publish('i18n://sv-se@b#draft')

    nodes = storage.get_many(('i18n://sv-se@a', 'i18n://sv-se@b'))
    for node in nodes.values():
        node.pop('meta')
    assert nodes == {
        'i18n://sv-se@a': {
            'uri': 'i18n://sv-se@a.txt#1',
            'content': u'A'
        },
        'i18n://sv-se@b': {
            'uri': 'i18n://sv-se@b.md#1',
            'content': u'B'
        }
    }


def test_delete():
    storage.set('i18n://sv-se@a.txt#draft', u'A')
    storage.set('i18n://sv-se@b.txt#draft', u'B')

    node = storage.get('i18n://sv-se@a#draft')
    assert node['content'] == u'A'

    deleted_node = storage.delete('sv-se@a#draft')
    deleted_node.pop('meta')
    assert deleted_node == {'uri': 'i18n://sv-se@a.txt#draft', 'content': u'A'}

    deleted_nodes = storage.delete_many(('sv-se@a#draft', 'sv-se@b#draft'))
    for node in deleted_nodes.values():
        node.pop('meta')
    assert deleted_nodes == {'i18n://sv-se@b#draft': {'uri': 'i18n://sv-se@b.txt#draft', 'content': u'B'}}


def test_nonexisting_node():
    with pytest.raises(URI.Invalid):
        storage.get('?')
    with pytest.raises(NodeDoesNotExist):
        storage.get('sv-se@page/title')


def test_plugin_mismatch():
    storage.set('i18n://sv-se@a.txt#draft', u'A')
    storage.publish('i18n://sv-se@a.txt#draft')

    with pytest.raises(NodeDoesNotExist):
        storage.get('i18n://sv-se@a.md')

    nodes = storage.get_many(('i18n://sv-se@a.md',))
    assert nodes == {}


def test_node_integrity():
    storage.backend._create(URI('i18n://sv-se@a.txt#draft'), u'first')
    with pytest.raises(PersistenceError):
        storage.backend._create(URI('i18n://sv-se@a'), u'second')
    with pytest.raises(PersistenceError):
        storage.backend._create(URI('i18n://sv-se@a.txt'), u'second')
    with pytest.raises(PersistenceError):
        storage.backend._create(URI('i18n://sv-se@a#draft'), u'second')
