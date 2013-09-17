import pytest
import threading
import cio
from cio import get_version
from cio.conf import settings, default_settings
from cio.pipeline import pipeline


def test_version():
    assert get_version((1, 2, 3, 'alpha', 1)) == '1.2.3a1'
    assert get_version((1, 2, 3, 'beta', 2)) == '1.2.3b2'
    assert get_version((1, 2, 3, 'rc', 3)) == '1.2.3c3'
    assert get_version((1, 2, 3, 'final', 4)) == '1.2.3'


def test_settings():
    assert settings.URI_NAMESPACE_SEPARATOR == default_settings.URI_NAMESPACE_SEPARATOR
    pre = settings.STORAGE
    with settings():
        settings.configure(STORAGE='bogus.newstorage')
        assert settings.STORAGE == 'bogus.newstorage'
    assert settings.STORAGE == pre


def test_environment():
    """
    'default': {
        'g11n': 'global',
        'i18n': (django_settings.LANGUAGE_CODE,),
        'l10n': (project_name(django_settings) or 'local',)
    }
    """
    env = settings.ENVIRONMENT
    assert env['default'] == {'g11n': 'global', 'i18n': 'sv-se', 'l10n': 'tests'}

    with pytest.raises(IndexError):
        cio.env.pop()

    with cio.env(i18n='sv', l10n=['loc'], g11n=('glob',)):
        assert cio.env.i18n == ('sv',)
        assert cio.env.l10n == ('loc',)
        assert cio.env.g11n == ('glob',)

    with pytest.raises(SystemError):
        cio.env.__init__()


# @pytest.mark.django_db(transaction=True)
def test_context():
    assert cio.env.state.i18n == ('sv-se',)

    with settings():
        settings.ENVIRONMENT['bogus'] = {
            'g11n': 'global',
            'i18n': ('sv', 'en'),
            'l10n': ('foo', 'bar')
        }

        with cio.env('bogus'):
            assert cio.env.state.i18n == ('sv', 'en')
            assert cio.env.state.l10n == ('foo', 'bar')

        with cio.env(i18n='en-us'):
            node = cio.get('i18n://label/firstname', lazy=False)
            buffered_node = cio.get('i18n://label/email')

            assert cio.env.i18n == ('en-us',)
            assert len(pipeline._buffer) == 1
            assert len(pipeline.history) == 1

            def assert_new_thread_env():
                assert cio.env.i18n == ('sv-se',)
                assert len(pipeline._buffer) == 0
                assert len(pipeline.history) == 0
                cio.get('i18n://label/surname', lazy=False)
                assert len(pipeline.history) == 1

            thread = threading.Thread(target=assert_new_thread_env)
            thread.start()
            thread.join()

            buffered_node.flush()
            assert len(pipeline._buffer) == 0
            assert len(pipeline.history) == 2
            assert pipeline.history.list('get') == [node, buffered_node._node]

    assert 'bogus' not in settings.ENVIRONMENT.keys()
