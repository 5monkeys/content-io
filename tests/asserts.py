from contextlib import contextmanager


@contextmanager
def assert_cache(calls=-1, hits=-1, misses=-1, sets=-1):
    from cio.backends import cache

    _cache = cache.backend  #._cache

    _cache.calls = 0
    _cache.hits = 0
    _cache.misses = 0
    _cache.sets = 0

    yield

    if calls >= 0:
        assert _cache.calls == calls
    if hits >= 0:
        assert _cache.hits == hits
    if misses >= 0:
        assert _cache.misses == misses
    if sets >= 0:
        assert _cache.sets == sets


@contextmanager
def assert_db(calls=-1, selects=-1, inserts=-1, updates=-1, deletes=-1):
    from cio.backends import storage
    backend = storage.backend
    backend.start_debug()

    yield

    count = lambda cmd: len([q for q in backend.queries if q['sql'].split(' ', 1)[0].upper().startswith(cmd)])
    if calls >= 0:
        assert len(backend.queries) == calls
    if selects >= 0:
        assert count('SELECT') == selects
    if inserts >= 0:
        assert count('INSERT') == inserts
    if updates >= 0:
        assert count('UPDATE') == updates
    if deletes >= 0:
        assert count('DELETE') == deletes

    backend.stop_debug()
