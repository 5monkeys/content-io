from __future__ import unicode_literals
from .txt import TextPlugin


class MarkdownPlugin(TextPlugin):

    ext = 'md'

    def render(self, data):
        import markdown
        if data:
            extensions = self.settings.get('EXTENSIONS', [])
            return markdown.markdown(data, extensions=extensions)
