# coding=utf-8
from __future__ import unicode_literals

import sys

PY26 = (sys.version_info[:2] == (2, 6))
VERSION = (1, 3, 0, 'beta', 1)


def get_version(version=None):
    """Derives a PEP386-compliant version number from VERSION."""
    if version is None:
        version = VERSION
    assert len(version) == 5
    assert version[3] in ('alpha', 'beta', 'rc', 'final')

    # Now build the two parts of the version number:
    # main = X.Y[.Z]
    # sub = .devN - for pre-alpha releases
    #     | {a|b|c}N - for alpha, beta and rc releases

    parts = 2 if version[2] == 0 else 3
    main = '.'.join(str(x) for x in version[:parts])

    sub = ''
    if version[3] != 'final':
        mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'c'}
        sub = mapping[version[3]] + str(version[4])

    return main + sub


__version__ = get_version()


class lazy_shortcut(object):
    def __init__(self, module, target):
        self._evaluated = False
        self.module = module
        self.targets = target.split('.', 1)

    def __call__(self, *args, **kwargs):
        target = self.__evaluate__()
        return target(*args, **kwargs)

    def __getattr__(self, item):
        target = self.__evaluate__()
        return getattr(target, item)

    def __evaluate__(self):
        if not self._evaluated:
            from .utils.imports import import_module

            # Evaluate target
            target = import_module(self.module)
            for name in self.targets:
                target = getattr(target, name)

            # Point module shortcut variable to target
            __module__ = sys.modules[__name__]
            setattr(__module__, name, target)

            self._evaluated = True
            return target


env = lazy_shortcut('cio.environment', 'env')
get = lazy_shortcut('cio.api', 'get')
set = lazy_shortcut('cio.api', 'set')
load = lazy_shortcut('cio.api', 'load')
delete = lazy_shortcut('cio.api', 'delete')
publish = lazy_shortcut('cio.api', 'publish')
revisions = lazy_shortcut('cio.api', 'revisions')
search = lazy_shortcut('cio.api', 'search')
