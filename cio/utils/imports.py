# coding=utf-8
from __future__ import unicode_literals

import sys


def import_module(package):
    __import__(package)
    return sys.modules[package]


def import_class(import_path, name=None):
    """
    Imports and returns class for full class path string.
    Ex. 'foo.bar.Bogus' -> <class 'foo.bar.Bogus'>
    """
    if not name:
        import_path, name = import_path.rsplit('.', 1)
    mod = import_module(import_path)
    try:
        return getattr(mod, name)
    except AttributeError as e:
        raise ImportError(e)
