#!/usr/bin/env python
from setuptools import setup, find_packages


tests_require = [
    'unittest2',
    'coverage',
    'Markdown'
]

version = __import__('cio').__version__

setup(
    name='content-io',
    version=version,
    description='Send content through a highly configurable pipeline including cache, plugin and storage pipes',
    long_description=(
        '.. image:: https://travis-ci.org/5monkeys/content-io.png?branch=master\n'
        '    :target: https://travis-ci.org/5monkeys/content-io\n'
        '.. image:: https://coveralls.io/repos/5monkeys/content-io/badge.png?branch=master\n'
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
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    extras_require={
        'tests': tests_require,
    },
    tests_require=tests_require,
    test_suite='runtests.main',
)
