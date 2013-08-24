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
