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
            assert cb.calls == calls
        if hits >= 0:
            assert cb.hits == hits
        if misses >= 0:
            assert cb.misses == misses
        if sets >= 0:
            assert cb.sets == sets


    @contextmanager
    def assertDB(self, calls=-1, selects=-1, inserts=-1, updates=-1, deletes=-1):
        from cio.backends import storage
        backend = storage.backend
        backend.start_debug()

        yield

        count = lambda cmd: len([q for q in backend.queries if q['sql'].split(' ', 1)[0].upper().startswith(cmd)])
        if calls >= 0:
            assert len(backend.queries) == calls
        if selects >= 0:
            assert count('SELECT') == selects
        if inserts >= 0:
            assert count('INSERT') == inserts
        if updates >= 0:
            assert count('UPDATE') == updates
        if deletes >= 0:
            assert count('DELETE') == deletes

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
