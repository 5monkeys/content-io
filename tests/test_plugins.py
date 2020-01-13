import cio
from cio.conf import settings
from cio.plugins import plugins
from cio.plugins import md as md_module
from cio.backends import storage
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
            'tests.UppercasePlugin'
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

    def test_replace_node_in_render_and_load(self):
        settings.configure(PLUGINS=[
            'cio.plugins.txt.TextPlugin',
            'cio.plugins.md.MarkdownPlugin',
            'tests.ReplacerPlugin'
        ])

        node = cio.set('sv-se@page/mine.rpl#1', "My own content")
        self.assertNotEqual(node.uri.path, 'page/mine.rpl')
        self.assertEqual(node.uri.path, 'page/rendered.rpl')
        self.assertEqual(node.content, 'REPLACED')

        node = cio.load('sv-se@page/loaded.rpl')
        self.assertEqual(node['uri'].path, 'page/loaded')

    def test_settings(self):
        settings.configure(TXT={
            'foo': 'bar'
        })

        plugin = plugins.get('txt')
        self.assertEqual(plugin.settings['foo'], 'bar')

    def test_markdown(self):
        markdown = plugins.get('md')
        self.assertEqual(markdown.render('# Title'), '<h1>Title</h1>')

    def test_markdown_handles_empty_data(self):
        markdown = plugins.get('md')
