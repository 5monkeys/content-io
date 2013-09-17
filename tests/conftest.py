import pytest


@pytest.fixture(scope='function', autouse=True)
def setup():
    from cio.environment import env
    from cio.backends import cache, storage
    from cio.pipeline import pipeline
    from cio.plugins import plugins

    env.reset()
    cache.clear()
    storage.backend._call_delete()
    pipeline.clear()
    plugins.load()


def pytest_configure():
    from cio.conf import settings
    settings.configure(
        ENVIRONMENT={
            'default': {
                'i18n': 'sv-se',
                'l10n': 'tests',
                'g11n': 'global'
            }
        },
    )
