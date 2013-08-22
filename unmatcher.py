"""
unmatcher :: Regular expression reverser for Python
"""
__version__ = "0.0.1"
__author__ = "Karol Kuczmarski"
__license__ = "Simplified BSD"


import random
import re
import string


__all__ = ['reverse']


def reverse(pattern, groups=None, **kwargs):
    if not isinstance(pattern, basestring):
        pattern = pattern.pattern  # assuming regex object
    regex_ast = re.sre_parse.parse(pattern).data

    groups = groups or {}

    reversal = Reversal(regex_ast, groups=groups, **kwargs)
    return reversal.perform()


# Implementation

class Reversal(object):

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
