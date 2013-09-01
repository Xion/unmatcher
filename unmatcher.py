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
    """Reverse the regular expression, returning a string that would match it.

    :param pattern: Regular expression pattern, either compiled one or a string

    Additional arguments (positional and keyword) will be used to supply
    predefined string matches for capture groups present in the ``pattern``.

    :return: String that matches ``pattern``
    """
    if isinstance(pattern, basestring):
        flags = None
    else:
        # assuming regex object
        flags = pattern.flags
        pattern = pattern.pattern

    sre_subpattern = re.sre_parse.parse(pattern)

    # use positional and keyword arguments, if any, to build the initial array
    # of capture group values that will be used by the reverser
    groupvals = kwargs or {}
    for i, value in enumerate(args, 1):
        if i in groupvals:
            raise TypeError(
                "reverse() got multiple values for capture group '%s'" % i)
        groupvals[i] = value
    groups = resolve_groupvals(sre_subpattern.pattern, groupvals)

    reversal = Reversal(sre_subpattern.data, flags=flags, groups=groups)
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

    # TODO: detect surplus keys in ``groupvals`` that do not match
    # any actual capture group inside ``sre_pattern``
    groups = [None] * group_count
    for ref, value in groupvals.iteritems():
        index = names2indices.get(ref, ref)
        try:
            groups[index] = value
        except (TypeError, IndexError):
            raise ValueError("invalid capture group reference: %s" % ref)

    return groups


class Reversal(object):
    """Encapsulates the reversal process of a single regular expression."""

    BUILTIN_CHARSETS = {
        'word': string.ascii_letters,
        'digit': string.digits,
        'space': string.whitespace,
    }
    MAX_REPEAT = 64

    def __init__(self, regex_ast, flags=None, groups=None):
        """Constructor.

        Use keywords to pass arguments other than ``regex_ast``.
        """
        self.regex_ast = regex_ast
        self.flags = flags or 0
        self.groups = groups or [None]

    def perform(self):
        return self._reverse_nodes(self.regex_ast)

    # Reversing regex AST nodes

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
            return random.choice(self._charset('any'))

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
        raise NotImplementedError(
            "unsupported regular expression element: %s" % type_)

    def _reverse_choice_node(self, node_data):
        """Generates string matching 'in' node from regular expr. AST.

        This node is an alternative between several variants (child nodes),
        incl. some that are not encountered in other places
        (character sets, for example).
        """
        first, _ = node_data[0]
        if first == 'negate':
            # TODO: support this
            raise NotImplementedError(
                "negated character sets [^...] are not supported")

        # TODO: charset variants might be of different size
        # (wrt to no. of chars they match), but they are all assigned
        # the same weight in the random.choice() below (along with non-charset
        # variants) - e.g. [a-cd] has the same chance to pick `a-c` or `d`;
        # see about correcting that (how about non-charset variants, though?)
        chosen = random.choice(node_data)
        type_, data = chosen

        # range (e.g. a-z) inside [ ]
        if type_ == 'range':
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

        charset = self._charset(type_)
        if negate:
            all_chars = self._charset('any', flags=0)
            charset = list(set(all_chars) - set(charset))
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

        if index is None:
            return self._reverse_nodes(nodes)  # non-capture group

        result = self.groups[index]
        if result is None:
            result = self.groups[index] = self._reverse_nodes(nodes)

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

    # Utility functions

    def _charset(self, name, flags=None):
        """Return chars belonging to charset of given name.
        :param flags: Optional flags override
        """
        flags = self.flags if flags is None else flags

        if name == 'any':
            if flags & re.DOTALL:
                return string.printable
            else:
                visible_chars = ''.join(
                    v for k, v in self.BUILTIN_CHARSETS.iteritems()
                    if k != 'space')
                return visible_chars + ' '

        if name in self.BUILTIN_CHARSETS:
            return self.BUILTIN_CHARSETS[name]

        raise ValueError("invalid charset name '%s'" % name)
