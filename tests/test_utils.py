from cio.utils.uri import URI


def test_uri():
    assert URI('i18n://sv@page/title.txt') == 'i18n://sv@page/title.txt'

    uri = URI(scheme='i18n', namespace='sv-se', path='page/title', ext='txt')
    assert uri == 'i18n://sv-se@page/title.txt'

    uri = URI('page/title')
    assert not uri.is_absolute()
    assert uri.scheme == 'i18n'
    assert uri.namespace is None
    assert uri.path == 'page/title'
    assert uri.ext is None

    uri = uri.clone(namespace='sv-se')
    assert not uri.is_absolute()
    assert uri == 'i18n://sv-se@page/title'

    uri = uri.clone(ext='txt')
    assert uri == 'i18n://sv-se@page/title.txt'
    assert uri.is_absolute()

    uri = URI('page/title')
    uri = uri.clone(scheme=None)
    assert uri == 'page/title'

    uri = URI('i18n://sv@page/title.txt#draft')
    assert uri == 'i18n://sv@page/title.txt#draft'
    assert uri.version == 'draft'
