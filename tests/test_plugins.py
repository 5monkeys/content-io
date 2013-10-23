import json
import cio
from cio.conf import settings
from cio.plugins import plugins
from cio.backends import storage
from cio.plugins.base import BasePlugin
from cio.plugins.exceptions import UnknownPlugin
from cio.plugins.txt import TextPlugin
from tests import BaseTest


class PluginTest(BaseTest):

    def test_resolve_plugin(self):
        with self.assertRaises(UnknownPlugin):
            plugins.get('xyz')

        plugin = plugins.resolve('i18n://sv-se@page/title.txt')
        self.assertIsInstance(plugin, TextPlugin)

        with self.assertRaises(UnknownPlugin):
            plugins.resolve('i18n://sv-se@page/title.foo')

    def test_register_plugin(self):
        with self.assertRaises(ImportError):
            plugins.register('foo.bar.BogusPlugin')
        with self.assertRaises(ImportError):
            plugins.register('cio.plugins.text.BogusPlugin')

    def test_plugin(self):
        self.assertSetEqual(set(plugins.plugins.keys()), set(['txt', 'md']))

        settings.configure(PLUGINS=[
            'cio.plugins.txt.TextPlugin',
            'cio.plugins.md.MarkdownPlugin',
            'tests.test_plugins.UppercasePlugin'
        ])

        self.assertSetEqual(set(plugins.plugins.keys()), set(['txt', 'md', 'up']))

        node = cio.set('sv-se@page/title.up', {'name': u'lundberg'}, publish=False)
        self.assertListEqual(node._content, [{'name': u'lundberg'}, u'{"name": "lundberg"}', u'LUNDBERG'])

        cio.publish(node.uri)

        node = cio.get('page/title')
        raw_content = storage.get(node.uri)

        self.assertIsNotNone(raw_content)
        self.assertEqual(raw_content['uri'], 'i18n://sv-se@page/title.up#1')
        self.assertEqual(raw_content['content'], u'{"name": "lundberg"}')
        self.assertEqual(node.content, u'LUNDBERG')
        self.assertEqual(node.uri.ext, 'up')

        self.assertSetEqual(set(p for p in plugins), set(('txt', 'md', 'up')))


class UppercasePlugin(BasePlugin):

    ext = 'up'

    def load(self, content):
        return json.loads(content) if content else None

    def save(self, data):
        return json.dumps(data)

    def render(self, data):
        return data['name'].upper()
