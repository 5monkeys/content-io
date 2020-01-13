import json
import six

if six.PY2:
    from unittest2 import TestCase
else:
    from unittest import TestCase

from contextlib import contextmanager
from cio.plugins.base import BasePlugin


class BaseTest(TestCase):

    def setUp(self):
        from cio.environment import env
        from cio.backends import cache, storage
        from cio.pipeline import pipeline
        from cio.plugins import plugins

        env.reset()
        cache.clear()
        storage.backend._call_delete()
        pipeline.clear()
        plugins.load()

        self.configure()

    def configure(self):
        from cio.conf import settings
        settings.configure(
            ENVIRONMENT={
                'default': {
                    'i18n': 'sv-se',
                    'l10n': 'tests',
                    'g11n': 'global'
                }
            },
            PLUGINS=[
                'cio.plugins.txt.TextPlugin',
                'cio.plugins.md.MarkdownPlugin'
            ]
        )

    def assertKeys(self, dict, *keys):
        self.assertEqual(set(dict.keys()), set(keys))

    @contextmanager
    def assertCache(self, calls=-1, hits=-1, misses=-1, sets=-1):
        from cio.backends import cache

        cb = cache.backend

        cb.calls = 0
        cb.hits = 0
        cb.misses = 0
        cb.sets = 0

        yield

        if calls >= 0:
            assert cb.calls == calls, '%s != %s' % (cb.calls, calls)
        if hits >= 0:
            assert cb.hits == hits, '%s != %s' % (cb.hits, hits)
        if misses >= 0:
            assert cb.misses == misses, '%s != %s' % (cb.misses, misses)
        if sets >= 0:
            assert cb.sets == sets, '%s != %s' % (cb.sets, sets)


    @contextmanager
    def assertDB(self, calls=-1, selects=-1, inserts=-1, updates=-1, deletes=-1):
        from cio.backends import storage
        backend = storage.backend
        backend.start_debug()

        yield

        count = lambda cmd: len([q for q in backend.queries if q['sql'].split(' ', 1)[0].upper().startswith(cmd)])
        if calls >= 0:
            call_count = len(backend.queries)
            assert call_count == calls, '%s != %s' % (call_count, calls)
        if selects >= 0:
            select_count = count('SELECT')
            assert select_count == selects, '%s != %s' % (select_count, selects)
        if inserts >= 0:
            insert_count = count('INSERT')
            assert insert_count == inserts, '%s != %s' % (insert_count, inserts)
        if updates >= 0:
            update_count = count('UPDATE')
            assert update_count == updates, '%s != %s' % (update_count, updates)
        if deletes >= 0:
            delete_count = count('DELETE')
            assert delete_count == deletes, '%s != %s' % (delete_count, deletes)

        backend.stop_debug()


class UppercasePlugin(BasePlugin):

    ext = 'up'

    def load(self, content):
        try:
            return json.loads(content) if content else None
        except ValueError:
            return content

    def save(self, data):
        if isinstance(data, dict):
            return json.dumps(data)
        else:
            return json.dumps(dict(name=data))

    def render(self, data):
        name = data if isinstance(data, six.string_types) else data['name']
        return name.upper()


class ReplacerPlugin(BasePlugin):

    ext = 'rpl'

    def _load(self, node):
        node.uri = node.uri.clone(path="page/loaded.rpl")
        node.content = "REPLACED"
        return self.load(node.content)

    def _render(self, node, data):
        node.uri = node.uri.clone(path="page/rendered.rpl")
        return self.render(data)