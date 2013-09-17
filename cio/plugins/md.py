from .txt import TextPlugin


class MarkdownPlugin(TextPlugin):

    ext = 'md'

    def render(self, data):
        # TODO: Handle markdown import error
        import markdown
        if data:
            return markdown.markdown(data)
