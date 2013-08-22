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

    BUILTIN_CHARSETS = {
        'any': string.printable,  # matches . (dot)
        'word': string.ascii_letters,
        'digit': string.digits,
        'space': string.whitespace,
    }
    MAX_REPEAT = 64

    def __init__(self, regex_ast, **kwargs):
        self.regex_ast = regex_ast
        self.groupdict = kwargs.get('groupdict', {})  # NYI

    def perform(self):
        # TODO: preserve unicodeness/ANSIness in Python 2
        return ''.join(map(self._reverse_node, self.regex_ast))

    def _reverse_node(self, (type_, data)):
        """Generates string matching given node from regular expression AST."""
        if type_ == 'literal':
            return chr(data)
        if type_ == 'any':
            return random.choice(self.BUILTIN_CHARSETS['any'])

        if type_ == 'in':
            return self._reverse_charset_node(data)
        if type_ in ('min_repeat', 'max_repeat'):
            return self._reverse_repeat_node(data)

        if type_ == 'at':
            return ''   # match-beginning (^) or match-end ($);
                        # irrelevant for string generation

        # TODO: add support for the rest of regex syntax elements
        raise ValueError("unsupported regular expression element: %s" % type_)

    def _reverse_charset_node(self, node_data):
        """Generates string matching 'in' node from regular expr. AST.

        This node matches a set of characters:

        * a built-in one (``\w``, ``\d``, etc.),
        * an ad-hoc one (``[a-z]``, ``[123abc]``, etc.),
        * or a combination of those (``[a-z\d])``, etc.)
        """
        chosen = random.choice(node_data)
        type_, data = chosen

        # range (e.g. a-z) inside [ ]
        if type_ == 'range':
            # TODO: add support for negation: [^...]
            min_char, max_char = data
            return chr(random.randint(min_char, max_char))

        # built-in character set: \d, \w, etc.
        if type_ == 'category':
            return self._reverse_builtin_charset_node(data)

        raise Exception("unexpected charset node: %s" % type_)

    def _reverse_builtin_charset_node(self, node_data):
        """Generates string matching 'category' node from regular expr. AST.

        This node matches a built-in set of characters, like ``\d`` or ``\w``.
        """
        _, type_ = node_data.rsplit('_', 1)  # category(_not)?_(digit|word|etc)
        negate = '_not_' in node_data

        charset = self.BUILTIN_CHARSETS[type_]
        if negate:
            charset = list(set(self.BUILTIN_CHARSETS['any']) - set(charset))
        return random.choice(charset)

    def _reverse_repeat_node(self, node_data):
        """Generates string matching 'min_repeat' or 'max_repeat' node
        from regular expression AST.

        This node matches a repetition of pattern matched by its child node.
        """
        # TODO: make sure if ``[what]`` is always a 1-element list
        min_count, max_count, [what] = node_data

        max_count = min(max_count, self.MAX_REPEAT)
        count = random.randint(min_count, max_count)
        return ''.join(self._reverse_node(what) for _ in xrange(count))
