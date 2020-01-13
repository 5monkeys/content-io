# coding=utf-8
import six
from cio import lazy_shortcut
from cio.conf import settings
from cio.utils.formatters import ContentFormatter
from cio.utils.uri import URI, quote
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

        with settings(URI_DEFAULT_SCHEME='l10n'):
            uri = URI('page/title')
            self.assertEqual(uri, 'l10n://page/title')
            self.assertEqual(uri.scheme, 'l10n')
        uri = uri.clone(scheme=None)
        self.assertEqual(uri, 'page/title')
        self.assertEqual(uri.scheme, None)

        uri = URI('i18n://sv@page/title.txt#draft')
        self.assertEqual(uri, 'i18n://sv@page/title.txt#draft')
        self.assertEqual(uri.version, 'draft')

    def test_uri_query_params(self):
        # Verify query params are snatched up
        uri = URI('i18n://sv@page/title.txt?var=someval')
        self.assertEqual(uri, 'i18n://sv@page/title.txt?var=someval')
        self.assertDictEqual(uri.query, {
            'var': ['someval']
        })

        # Verify query params work with version
        uri = URI('i18n://sv@page/title.txt?var=someval#2')
        self.assertEqual(uri, 'i18n://sv@page/title.txt?var=someval#2')
        self.assertDictEqual(uri.query, {
            'var': ['someval']
        })

        # Verify multiple query parameters are handled
        uri = URI('i18n://sv@page/title.txt?var=someval&second=2')
        self.assertEqual(uri, 'i18n://sv@page/title.txt?var=someval&second=2')
        self.assertDictEqual(uri.query, {
            'var': ['someval'],
            'second': ['2'],
        })

        # Verify query params can be replaced when cloned
        uri = uri.clone(query={
            'var': ['newval'],
            'second': ['1']
        })
        self.assertDictEqual(uri.query, {
            'var': ['newval'],
            'second': ['1']
        })
        exact_copy = uri.clone()
        self.assertEqual(exact_copy, uri)
        self.assertDictEqual(exact_copy.query, uri.query)
        self.assertEqual(exact_copy.query['second'], ['1'])
        self.assertNotEqual(id(exact_copy.query), id(uri.query))

        # Verify replacement works
        uri = URI('i18n://sv@page/title.txt?var=someval&second=2').clone(query=None)
        self.assertEqual(uri.query, None)

        # Verify unicode strings are handled correctly
        value = quote(u'räv')
        unicode_uri = u'i18n://sv@page/title.txt?fox=' + value
        uri = URI(unicode_uri.encode('utf-8'))
        self.assertEqual(uri, unicode_uri)
        self.assertDictEqual(uri.query, {
            u'fox': [u'räv']
        })

        # Verify query parameter order
        uri = URI(b'i18n://sv@page/title.txt?fox=1&variable=2&last=3')
        self.assertEqual(uri, 'i18n://sv@page/title.txt?fox=1&variable=2&last=3')
        self.assertDictEqual(uri.query, {
            'fox': ['1'],
            'variable': ['2'],
            'last': ['3']
        })

        # Verify empty variables are handled correctly
        uri = URI(u'i18n://sv@page/title.txt?fox=&variable')
        self.assertEqual(uri, 'i18n://sv@page/title.txt?fox=&variable=')
        self.assertDictEqual(uri.query, {
            'fox': [],
            'variable': []
        })

        # Verify delimiters as values and/or keys
        value = quote(u'i18n://sv@page/title.txt#1')
        unicode_uri = u'i18n://sv@page/title.txt?fox=' + value
        uri = URI(unicode_uri.encode('utf-8'))
        self.assertEqual(uri, unicode_uri)
        self.assertDictEqual(uri.query, {
            'fox': [u'i18n://sv@page/title.txt#1']
        })

        # Verify multiple query params with same key return last entry
        uri = URI('i18n://sv@page/title.txt?key=a&key=b&key=c')
        self.assertEqual(uri, 'i18n://sv@page/title.txt?key=c')
        self.assertDictEqual(uri.query, {
            'key': ['c']
        })

        # Verify query string handles when no values are inputted
        uri = URI('i18n://sv@page/title.txt?')
        self.assertEqual(uri, 'i18n://sv@page/title.txt')
        self.assertEqual(uri.query, None)

        # Verify query string handles when keys without values are inputted
        uri = URI('i18n://sv@page/title.txt?key')
        self.assertEqual(uri, 'i18n://sv@page/title.txt?key=')
        self.assertEqual(uri.query, {
            'key': []
        })

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
