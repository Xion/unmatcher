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


def reverse(pattern, *args, **kwargs):
    if not isinstance(pattern, basestring):
        pattern = pattern.pattern  # assuming regex object

    sre_subpattern = re.sre_parse.parse(pattern)

    # use positional and keyword arguments, if any, to build the initial array
    # of capture group values that will be used by the reverser
    groupvals = kwargs or {}
    for i, value in enumerate(args, 1):
        if i in groupvals:
            raise TypeError(
                "reverse() got multiple values for capture group '%s'" % i)
        groupvals[i] = value
    groups = resolve_groupvals(sre_subpattern.pattern, kwargs or {})

    reversal = Reversal(regex_ast=sre_subpattern.data, groups=groups, **kwargs)
    return reversal.perform()


# Implementation

def resolve_groupvals(sre_pattern, groupvals):
    """Resolve a dictionary of capture group values (mapped from either
    their names or indices), returning an array of those values ("mapped" only
    from capture groups indices).

    :param sre_pattern: A ``sre_parse.Pattern`` object
    :param groupvals: Dictionary mapping capture group names **or** indices
                      into string values for those groups
    """
    group_count = sre_pattern.groups
    names2indices = sre_pattern.groupdict

    groups = [None] * group_count
    for ref, value in groupvals.iteritems():
        index = names2indices.get(ref, ref)
        try:
            groups[index] = value
        except (TypeError, IndexError):
            raise ValueError("invalid capture group reference: %s" % ref)

    return groups


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
        self.groups = kwargs.get('groups', [None])  # NYI

    def perform(self):
        return self._reverse_nodes(self.regex_ast)

    def _reverse_nodes(self, nodes):
        """Generates string matching given sequence of nodes
        from regular expressions' abstract syntax tree (AST).
        """
        # TODO: preserve unicodeness/ANSIness in Python 2
        return ''.join(map(self._reverse_node, nodes))

    def _reverse_node(self, (type_, data)):
        """Generates string matching given node from regular expression AST."""
        if type_ == 'literal':
            return chr(data)
        if type_ == 'any':
            return random.choice(self.BUILTIN_CHARSETS['any'])

        if type_ == 'in':
            return self._reverse_choice_node(data)
        if type_ == 'branch':
            return self._reverse_branch_node(data)

        if type_ in ('min_repeat', 'max_repeat'):
            return self._reverse_repeat_node(data)

        if type_ == 'subpattern':
            return self._reverse_subpattern_node(data)
        if type_ == 'groupref':
            return self._reverse_groupref_node(data)

        if type_ == 'at':
            return ''   # match-beginning (^) or match-end ($);
                        # irrelevant for string generation

        # TODO: add support for the rest of regex syntax elements
        raise ValueError("unsupported regular expression element: %s" % type_)

    def _reverse_choice_node(self, node_data):
        """Generates string matching 'in' node from regular expr. AST.

        This node is an alternative between several variants (child nodes),
        incl. some that are not encountered in other places
        (character sets, for example).
        """
        # TODO: charset variants might be of different size
        # (wrt to no. of chars they match), but they are all assigned
        # the same weight in the random.choice() below (along with non-charset
        # variants) - e.g. [a-cd] has the same chance to pick `a-c` or `d`;
        # see about correcting that (how about non-charset variants, though?)
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

        return self._reverse_node(chosen)

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
        return self._reverse_nodes([what] * count)

    def _reverse_branch_node(self, node_data):
        """Generates string matching 'branch' node in regular expr. AST.

        This node is similar to 'in', in a sens that it's also an alternative
        between several variants. However, each variant here can consist
        of more then one node.
        """
        # TODO: figure out what the first value is; for all typical expressions
        # (a|bb|c, etc.) it seems to be always ``None``
        _, variants = node_data

        nodes = random.choice(variants)
        return self._reverse_nodes(nodes)

    def _reverse_subpattern_node(self, node_data):
        """Generates string matching 'subpattern' node in regular expr. AST.

        This node corresponds to parenthesised group inside the expression.
        If this is a capture group, the reversed result is memorized
        so that it can be used when referring back to the capture through
        ``\1``, etc.
        """
        index, nodes = node_data

        # reverse subpattern and remember the result if it's new capture group
        result = self._reverse_nodes(nodes)
        if index is not None and self.groups[index] is None:
            self.groups[index] = result

        return result

    def _reverse_groupref_node(self, node_data):
        """Generates string matching 'groupref' node in regular expr. AST.

        This node is a (back)reference to previously matched capture group.
        """
        # AST always refers to capture groups by index,
        # and detects circular/forward references at parse time,
        # so handling of this node can be indeed very simple
        index = node_data
        return self.groups[index]
