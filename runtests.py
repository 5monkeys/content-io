#!/usr/bin/env python
import logging
import os
import sys
import six

if six.PY3:
    from unittest import defaultTestLoader as TestLoader, TestSuite, TextTestRunner as TestRunner
else:
    from unittest2 import defaultTestLoader as TestLoader, TestSuite, TextTestRunner as TestRunner


def main():
    # Configure python path
    parent = os.path.dirname(os.path.abspath(__file__))
    if not parent in sys.path:
        sys.path.insert(0, parent)

    # Configure logging
    logging.basicConfig(level=logging.ERROR)

    # Configure setup
    from cio.conf import settings
    settings.configure(STORAGE={
        'BACKEND': 'sqlite://',
        'NAME': ':memory:',
        'OPTIONS': {
            'check_same_thread': False
        }
    })

    # Run tests
    tests = TestLoader.discover('tests')
    suite = TestSuite(tests)
    result = TestRunner(verbosity=1, failfast=False).run(suite)
    exit_code = len(result.failures) + len(result.errors)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
