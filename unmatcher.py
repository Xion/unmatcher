"""
unmatcher
=========

Regular expression reverser for Python

:author: Karol Kuczmarski "Xion"
"""
import random
import re


__all__ = ['reverse', 'Unmatcher']


def reverse(regex):
    return Unmatcher(regex).reverse()


class Unmatcher(object):

    def __init__(self, pattern):
        if not isinstance(pattern, basestring):
            pattern = pattern.pattern  # assuming regex object
        self.regex_ast = re.sre_parse.parse(pattern).data

    def __call__(self, *args, **kwargs):
        return self.reverse(*args, **kwargs)

    def reverse(self, groups=None, **kwargs):
        reversal = RegexReversal(self.regex_ast,
                                 groups=groups or {}, **kwargs)
        return reversal.perform()


# Implementation

class RegexReversal(object):

    def __init__(self, regex_ast, **kwargs):
        self.regex_ast = regex_ast
        self.capture_groups = kwargs.get('groups', {})  # NYI

    def perform(self):
        # TODO: preserve unicodeness/ANSIness in Python 2
        return ''.join(map(self._reverse_node, self.regex_ast))

    def _reverse_node(self, (type_, data)):
        if type_ == 'literal':
            return chr(data)

        raise ValueError("unsupported regular expression element: %s" % type_)
