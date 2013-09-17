class BasePlugin(object):

    ext = None

    def load(self, content):
        """
        Return plugin data for content string
        """
        return content

    def save(self, data):
        """
        Persist external plugin resources and return content string for plugin data
        """
        return data

    def delete(self, data):
        """
        Delete external plugin resources
        """
        pass

    def render(self, data):
        """
        Render plugin
        """
        return data
