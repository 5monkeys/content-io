from cio.utils.uri import URI
from tests import BaseTest


class UtilsTest(BaseTest):

    def test_uri(self):
        self.assertEqual(URI('i18n://sv@page/title.txt'), 'i18n://sv@page/title.txt')

        uri = URI(scheme='i18n', namespace='sv-se', path='page/title', ext='txt')
        self.assertEqual(uri, 'i18n://sv-se@page/title.txt')

        uri = URI('page/title')
        self.assertFalse(uri.is_absolute())
        self.assertEqual(uri.scheme, 'i18n')
        self.assertIsNone(uri.namespace)
        self.assertEqual(uri.path, 'page/title')
        self.assertIsNone(uri.ext)

        uri = uri.clone(namespace='sv-se')
        self.assertFalse(uri.is_absolute())
        self.assertEqual(uri, 'i18n://sv-se@page/title')

        uri = uri.clone(ext='txt')
        self.assertEqual(uri, 'i18n://sv-se@page/title.txt')
        self.assertTrue(uri.is_absolute())

        uri = URI('page/title')
        uri = uri.clone(scheme=None)
        self.assertEqual(uri, 'page/title')

        uri = URI('i18n://sv@page/title.txt#draft')
        self.assertEqual(uri, 'i18n://sv@page/title.txt#draft')
        self.assertEqual(uri.version, 'draft')
