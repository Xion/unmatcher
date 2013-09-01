unmatcher
=========

*unmatcher* tries to solve the following problem:

    *Given a regular expression, find any string that matches the expression.*

Although very doable when talking about regexes known from computational linguistics,
the real world regular expressions are much more powerful to allow for that... easily.

Why do that, though? Well, mostly just because. One possible application could be
in automatic generation of test cases for string processing functions.


Status
~~~~~~

Most typical elements of regexes are supported:
``*``, ``+``, ``|``, ``( )`` (capture groups), ``\d|\w|\s`` (character classes), ``[]`` (character sets).


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

Note that predefined value is *not* validated against actual subexpression for the capture group.
