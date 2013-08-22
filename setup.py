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
    long_description=__doc__,
    author=unmatcher.__author__,
    url="http://xion.io/unmatcher",
    license=unmatcher.__license__,

    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        # TODO: add more domain-specific classifiers
    ],

    platforms='any',
    py_modules=['unmatcher'],
)
