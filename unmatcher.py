"""
unmatcher
=========

Regular expression reverser for Python

:author: Karol Kuczmarski "Xion"
"""
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

    def reverse(self):
        raise NotImplementedError()
