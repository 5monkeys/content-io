# coding=utf-8
from cio import lazy_shortcut
from cio.utils.formatters import ContentFormatter
from cio.utils.uri import URI
from cio.utils.imports import import_class
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

        uri = uri.clone(path='images/me.jpg/title', version='draft')
        self.assertEqual(uri, 'i18n://sv-se@images/me.jpg/title.txt#draft')
        self.assertEqual(uri.version, 'draft')
        self.assertEqual(uri.path, 'images/me.jpg/title')
        self.assertEqual(uri.ext, 'txt')

        uri = uri.clone(ext=None)
        self.assertEqual(uri, 'i18n://sv-se@images/me.jpg/title#draft')
        self.assertIsNone(uri.ext)

        uri = URI('page/title')
        uri = uri.clone(scheme=None)
        self.assertEqual(uri, 'page/title')

        uri = URI('i18n://sv@page/title.txt#draft')
        self.assertEqual(uri, 'i18n://sv@page/title.txt#draft')
        self.assertEqual(uri.version, 'draft')

    def test_formatter(self):
        tests = [
            (u"These are no variables: {} {0} {x} {x:f} {x!s} {x!r:.2f} { y } {{ y }}", {}, None),
            (u"This is no variable {\n\t'foo!': 'bar', ham: 'spam'\n}", {}, None),
            (u"These are variabls {v}, {n!s}, {n:.2f}, {n!s:>5}", dict(v=u'VALUE', n=1),
             u"These are variabls VALUE, 1, 1.00,     1"),
            (u"This is {mixed} with variables {}, {x}", dict(x=u'X'),
             u"This is {mixed} with variables {}, X")
        ]

        formatter = ContentFormatter()

        for template, context, value in tests:
            self.assertEqual(formatter.format(template, **context), value or template)

    def test_import_class(self):
        CF = import_class('cio.utils.formatters', 'ContentFormatter')
        self.assertEqual(CF, ContentFormatter)

        with self.assertRaises(ImportError):
            import_class('cio.utils.formatters', 'FooBar')

    def test_lazy_shortcut(self):
        uri_module = lazy_shortcut('cio.utils', 'uri')
        self.assertEqual(uri_module.URI, URI)
