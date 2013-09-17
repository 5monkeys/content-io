import json
import pytest
import cio
from cio.plugins import plugins
from cio.backends import storage
from cio.plugins.base import BasePlugin
from cio.plugins.exceptions import UnknownPlugin
from cio.plugins.txt import TextPlugin


def test_resolve_plugin():
    with pytest.raises(UnknownPlugin):
        plugins.get('xyz')

    plugin = plugins.resolve('i18n://sv-se@page/title.txt')
    assert isinstance(plugin, TextPlugin)

    with pytest.raises(UnknownPlugin):
        plugins.resolve('i18n://sv-se@page/title.foo')


def test_register_plugin():
    with pytest.raises(ImportError):
        plugins.register('foo.bar.BogusPlugin')
    with pytest.raises(ImportError):
        plugins.register('cio.plugins.text.BogusPlugin')


# @pytest.mark.django_db(transaction=True)
def test_plugin():
    plugins.register(UppercasePlugin)

    node = cio.set('sv-se@page/title.up', {'name': u'lundberg'}, publish=False)
    assert node._content == [{'name': u'lundberg'}, u'{"name": "lundberg"}', u'LUNDBERG']

    cio.publish(node.uri)

    node = cio.get('page/title.up')
    raw_content = storage.get(node.uri)

    assert raw_content['uri'] == 'i18n://sv-se@page/title.up#1'
    assert raw_content['content'] == u'{"name": "lundberg"}'
    assert node.content == u'LUNDBERG'
    assert node.uri.ext == 'up'


class UppercasePlugin(BasePlugin):

    ext = 'up'

    def load(self, content):
        return json.loads(content)
        # return content.rstrip('.saved')

    def save(self, data):
        return json.dumps(data)
        # return data + '.saved'

    def render(self, data):
        return data['name'].upper()
