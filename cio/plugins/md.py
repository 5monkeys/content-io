from __future__ import unicode_literals

import logging

from .txt import TextPlugin
from .. import PY26


class MarkdownPlugin(TextPlugin):

    ext = 'md'

    def render(self, data):
        if PY26:
            logging.warning('Markdown is not supported for Python 2.6')
            return data
        else:
            import markdown
            if data:
                extensions = self.settings.get('EXTENSIONS', [])
                return markdown.markdown(data, extensions=extensions)
