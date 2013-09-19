#!/usr/bin/env python
import codecs
import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


version = __import__('cio').__version__

setup(
    name='content-io',
    version=version,
    description='Send content through a highly configurable pipeline including cache, plugin and storage pipes',
    long_description=codecs.open(
        os.path.join(
            os.path.dirname(__file__),
            'README.md'
        )
    ).read(),
    author='Jonas Lundberg',
    author_email='jonas@5monkeys.se',
    url='https://github.com/5monkeys/content-io',
    download_url='https://github.com/5monkeys/content-io/tarball/%s' % version,
    keywords=['cms', 'content', 'management', 'pipeline', 'plugin', 'backend', 'cache', 'storage'],
    license='BSD',
    packages=find_packages(exclude='tests'),
    classifiers=[
        'Environment :: Web Environment',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    tests_require=['pytest', 'markdown'],
    test_suite='tests',
    cmdclass={'test': PyTest},
)
