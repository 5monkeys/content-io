# coding=utf-8
import cio
from cio import events
from cio.utils.uri import URI
from cio.utils.imports import import_class
from tests import BaseTest


def callback(a, b, **kwargs):
    assert a == 'a'
    assert b == 'b'
    assert set(kwargs.keys()) == {'c', 'd'}
    assert kwargs['c'] == 'c'
    kwargs['d']['called'] += 1  # callback answer


class EventsTest(BaseTest):

    def tearDown(self):
        events.clear()

    def test_listen(self):
        d = dict(called=0)
        events.listen('foo', callback)
        events.trigger('foo', 'a', 'b', c='c', d=d)
        self.assertEqual(d['called'], 1)

    def test_mute(self):
        d = dict(called=0)
        events.listen('foo', callback)
        events.mute('foo', callback)
        d['called'] = 0
        events.trigger('foo', 'a', 'b', c='c', d=d)
        self.assertEqual(d['called'], 0)

    def test_publish(self):
        def publish_callback(nodes):
            self.assertEqual(len(nodes), 1)
            node = nodes[0]
            self.assertEqual(node.uri, 'i18n://sv-se@foo/bar.txt#1')

        events.listen('publish', publish_callback)

        node = cio.set('sv-se@foo/bar', u'baz', publish=False)
        node = cio.publish(node.uri)
