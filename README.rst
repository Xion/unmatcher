unmatcher
=========

*unmatcher* tries to solve the following problem:

    *Given a regular expression, find any string that matches the expression.*

Why? Mostly just because. But one possible application is to generate test data for string processing functions.


Status
~~~~~~

|Version| |License| |Build Status|

.. |Version| image:: https://badge.fury.io/py/unmatcher.png
   :alt: PyPI package version
   :target: http://badge.fury.io/py/unmatcher
.. |License| image:: https://img.shields.io/pypi/l/unmatcher.svg?style=flat
    :target: https://github.com/Xion/unmatcher/blob/master/LICENSE
    :alt: License
.. |Build Status| image:: https://secure.travis-ci.org/Xion/unmatcher.png
   :alt: Build Status
   :target: http://travis-ci.org/Xion/unmatcher

Most typical elements of regexes are supported:

* multipliers: ``*``, ``+``
* capture groups: ``|``, ``( )`` (including backreferences)
* character classes (``\d|\w|\s`` etc.) and character sets (``[]``)


API
~~~

``unmatcher`` module exposes a single ``reverse`` function.
It takes a regular expression - either in text or compiled form - and returns a random string that matches it::

    >>> import unmatcher
    >>> print unmatcher.reverse(r'\d')
    7

Additional arguments can be provided, specifying predefined values for capture groups
inside the expression. Use positional arguments for numbered groups (``'\1'``, etc.)::

    >>> import unmatcher
    >>> print unmatcher.reverse(r'<(\w+)>.*</\1>', 'h1')
    <h1>1NLNVlrOT4YGyHV3vD7cHvrAl8OHVWDPKgmaE4gUsctboyFYUx</h1>

and keyword arguments for named groups::

    >>> import unmatcher
    >>> print unmatcher.reverse('(?P<foo>\w+)__(?P=foo)', foo='bar')
    bar__bar

Note that a predefined value is *not* validated against actual subexpression for the capture group.
