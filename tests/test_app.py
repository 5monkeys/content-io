import threading
import cio
from cio import get_version
from cio.conf import settings, default_settings
from cio.pipeline import pipeline
from tests import BaseTest


class AppTest(BaseTest):

    def test_version(self):
        self.assertEqual(get_version((1, 2, 3, 'alpha', 1)), '1.2.3a1')
        self.assertEqual(get_version((1, 2, 3, 'beta', 2)), '1.2.3b2')
        self.assertEqual(get_version((1, 2, 3, 'rc', 3)), '1.2.3c3')
        self.assertEqual(get_version((1, 2, 3, 'final', 4)), '1.2.3')

    def test_settings(self):
        self.assertEqual(settings.URI_NAMESPACE_SEPARATOR, default_settings.URI_NAMESPACE_SEPARATOR)
        pre = settings.STORAGE
        with settings():
            settings.configure(STORAGE='bogus.newstorage')
            self.assertEqual(settings.STORAGE, 'bogus.newstorage')
        self.assertEqual(settings.STORAGE, pre)

        self.assertEqual(settings.STORAGE['NAME'], ':memory:', "Should've been overridden")

        settings.STORAGE['PIPE'] = {'FOO': 'bar'}
        def assert_local_thread_settings():
            settings.configure(local=True, STORAGE={'PIPE': {'HAM': 'spam'}})
            self.assertEqual(settings.STORAGE['PIPE']['FOO'], 'bar')
            self.assertEqual(settings.STORAGE['PIPE']['HAM'], 'spam')

        thread = threading.Thread(target=assert_local_thread_settings)
        thread.start()
        thread.join()

        self.assertEqual(settings.STORAGE['PIPE']['FOO'], 'bar')
        self.assertNotIn('HAM', settings.STORAGE['PIPE'])

    def test_environment(self):
        """
        'default': {
            'g11n': 'global',
            'i18n': (django_settings.LANGUAGE_CODE,),
            'l10n': (project_name(django_settings) or 'local',)
        }
        """
        env = settings.ENVIRONMENT
        self.assertDictEqual(env['default'], {'g11n': 'global', 'i18n': 'sv-se', 'l10n': 'tests'})

        with self.assertRaises(IndexError):
            cio.env.pop()

        with cio.env(i18n='sv', l10n=['loc'], g11n=('glob',)):
            self.assertTupleEqual(cio.env.i18n, ('sv',))
            self.assertTupleEqual(cio.env.l10n, ('loc',))
            self.assertTupleEqual(cio.env.g11n, ('glob',))

        with self.assertRaises(SystemError):
            cio.env.__init__()

    def test_context(self):
        self.assertTupleEqual(cio.env.state.i18n, ('sv-se',))

        with settings():
            settings.ENVIRONMENT['bogus'] = {
                'g11n': 'global',
                'i18n': ('sv', 'en'),
                'l10n': ('foo', 'bar')
            }

            with cio.env('bogus'):
                self.assertTupleEqual(cio.env.state.i18n, ('sv', 'en'))
                self.assertTupleEqual(cio.env.state.l10n, ('foo', 'bar'))

            with cio.env(i18n='en-us'):
                node = cio.get('i18n://label/firstname', lazy=False)
                buffered_node = cio.get('i18n://label/email')

                self.assertTupleEqual(cio.env.i18n, ('en-us',))
                self.assertEqual(len(pipeline._buffer), 1)
                self.assertEqual(len(pipeline.history), 1)

                def assert_new_thread_env():
                    self.assertTupleEqual(cio.env.i18n, ('sv-se',))
                    self.assertEqual(len(pipeline._buffer), 0)
                    self.assertEqual(len(pipeline.history), 0)
                    cio.get('i18n://label/surname', lazy=False)
                    self.assertEqual(len(pipeline.history), 1)

                thread = threading.Thread(target=assert_new_thread_env)
                thread.start()
                thread.join()

                buffered_node.flush()
                self.assertEqual(len(pipeline._buffer), 0)
                self.assertEqual(len(pipeline.history), 2)
                self.assertListEqual(pipeline.history.list('get'), [node, buffered_node._node])

        self.assertNotIn('bogus', settings.ENVIRONMENT.keys())
