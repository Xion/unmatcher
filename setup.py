#!/usr/bin/env python
"""
unmatcher
=========

Regular expression reverser for Python
"""
from setuptools import setup

import unmatcher


setup(
    name="unmatcher",
    version=unmatcher.__version__,
    description="Regular expression reverser for Python",
    long_description=open('README.rst').read(),
    author=unmatcher.__author__,
    url="http://github.com/Xion/unmatcher",
    license=unmatcher.__license__,

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Testing",
        "Topic :: Text Processing :: General",
    ],

    platforms='any',
    py_modules=['unmatcher'],

    tests_require=['pytest', 'pytest-quickcheck'],
)
