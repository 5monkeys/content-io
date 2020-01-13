#!/usr/bin/env python
from setuptools import setup, find_packages
from sys import version_info

install_requires = [
    'six',
]

tests_require = [
    'coverage',
    'Markdown'
]

if version_info < (3,):
    tests_require += ['unittest2']

version = __import__('cio').__version__

setup(
    name='content-io',
    version=version,
    description='Send content through a highly configurable pipeline including cache, plugin and storage pipes',
    long_description=(
        '.. image:: https://travis-ci.org/5monkeys/content-io.svg?branch=master\n'
        '    :target: https://travis-ci.org/5monkeys/content-io\n'
        '.. image:: https://coveralls.io/repos/5monkeys/content-io/badge.svg?branch=master\n'
        '    :target: https://coveralls.io/r/5monkeys/content-io?branch=master\n\n'
    ),
    author='Jonas Lundberg',
    author_email='jonas@5monkeys.se',
    url='https://github.com/5monkeys/content-io',
    download_url='https://github.com/5monkeys/content-io/tarball/%s' % version,
    keywords=['cms', 'content', 'management', 'pipeline', 'plugin', 'backend', 'cache', 'storage'],
    license='BSD',
    packages=find_packages(exclude='tests'),
    include_package_data=False,
    zip_safe=False,
    classifiers=[
        'Environment :: Web Environment',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=install_requires,
    extras_require={
        'tests': tests_require,
    },
    tests_require=tests_require,
    test_suite='runtests.main',
)
