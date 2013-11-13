"""
unmatcher :: Regular expression reverser for Python
"""
__version__ = "0.1.3"
__author__ = "Karol Kuczmarski"
__license__ = "Simplified BSD"


import random
import re
import string
import sys


# Python 2/3 compatibility shims
IS_PY3 = sys.version[0] == '3'
if IS_PY3:
    imap = map
    unichr = chr
    xrange = range
else:
    from itertools import imap


__all__ = ['reverse']


def reverse(pattern, *args, **kwargs):
    """Reverse the regular expression, returning a string that would match it.

    :param pattern: Regular expression pattern, either compiled one or a string

    Additional arguments (positional and keyword) will be used to supply
    predefined string matches for capture groups present in the ``pattern``.

    :return: String that matches ``pattern``
    """
    if is_string(pattern):
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

    reversal = Reversal(sre_subpattern.data, flags=flags, groups=groups,
                        string_class=type(pattern))
    return reversal.perform()


# Implementation

is_string = lambda x: isinstance(x, (str if IS_PY3 else basestring))


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
    for ref, value in groupvals.items():
        try:
            index = names2indices[ref] if is_string(ref) else ref
            groups[index] = value
        except (IndexError, KeyError, TypeError):
            raise ValueError("invalid capture group reference: %s" % ref)

    return groups


class Reversal(object):
    """Encapsulates the reversal process of a single regular expression."""

    # TODO: choose among Unicode characters if using Unicode
    BUILTIN_CHARSETS = {
        'word': string.ascii_letters + string.digits,
        'digit': string.digits,
        'space': string.whitespace,
    }
    MAX_REPEAT = 64

    def __init__(self, regex_ast, flags=None, groups=None, string_class=None):
        """Constructor.

        Use keywords to pass arguments other than ``regex_ast``.
        """
        self.regex_ast = regex_ast
        self.flags = flags or 0
        self.groups = groups or [None]

        # use correct string class depending on Python version or argument
        if string_class is None:
            string_class = str if IS_PY3 else unicode
        self._str = string_class
        self._chr = unichr if string_class.__name__ == 'unicode' else chr

    def perform(self):
        return self._reverse_nodes(self.regex_ast)

    # Reversing regex AST nodes

    def _reverse_nodes(self, nodes):
        """Generates string matching given sequence of nodes
        from regular expressions' abstract syntax tree (AST).
        """
        return self._str().join(imap(self._reverse_node, nodes))

    def _reverse_node(self, node):
        """Generates string matching given node from regular expression AST."""
        type_, data = node

        if type_ == 'literal':
            return self._reverse_literal_node(data)
        if type_ == 'not_literal':
            return self._reverse_not_literal_node(data)
        if type_ == 'any':
            return random.choice(self._charset('any'))

        if type_ == 'in':
            return self._reverse_in_node(data)
        if type_ == 'branch':
            return self._reverse_branch_node(data)

        if type_ in ('min_repeat', 'max_repeat'):
            return self._reverse_repeat_node(data)

        if type_ == 'subpattern':
            return self._reverse_subpattern_node(data)
        if type_ == 'groupref':
            return self._reverse_groupref_node(data)
        if type_ == 'groupref_exists':
            return self._reverse_groupref_exists_node(data)

        if type_ in ('assert', 'assert_not'):
            # TODO: see whether these are in any way relevant
            # to string generation and support them if so
            raise NotImplementedError(
                "lookahead/behind assertion are not supported")
        if type_ == 'at':
            return ''   # match-beginning (^) or match-end ($);
                        # irrelevant for string generation

        raise NotImplementedError(
            "unsupported regular expression element: %s" % type_)

    def _reverse_literal_node(self, node_data):
        """Generates string matching the 'literal' node from regexp. AST.

        This node matches a literal character, a behavior which may optionally
        be modified by certain regular expressions flags.
        """
        char = self._chr(node_data)
        if self.flags & re.IGNORECASE:
            case_func = random.choice((self._str.lower, self._str.upper))
            char = case_func(char)
        return char

    def _reverse_not_literal_node(self, node_data):
        """Generates string matching the 'not_literal' node from regexp. AST.

        This node matches characters *expect* for given one, which corresponds
        to ``[^X]`` syntax, where ``X`` is a character.
        """
        excluded = self._chr(node_data)
        if self.flags & re.IGNORECASE:
            excluded = (excluded.lower(), excluded.upper())
        return random.choice(self._negate(excluded))

    def _reverse_in_node(self, node_data):
        """Generates string matching 'in' node from regular expr. AST.

        This node matches a specified set of characters. Typically,
        it is expressed using the ``[...]`` notation, but it can also arise
        from simple uses of ``|`` operator, where all branches match
        just one, literal character (e.g. ``a|b|c``).
        """
        negate = node_data[0][0] == 'negate'
        if negate:
            node_data = node_data[1:]

        charset = set()
        for type_, data in node_data:
            if type_ == 'literal':
                charset.add(self._chr(data))
            elif type_ == 'range':
                min_char, max_char = data
                charset.update(imap(self._chr, xrange(min_char, max_char + 1)))
            elif type_ == 'category':
                _, what = data.rsplit('_', 1)  # category(_not)?_(digit|word|etc)
                category_chars = self._charset(what)
                if '_not_' in data:
                    category_chars = self._negate(category_chars)
                charset.update(category_chars)
            else:
                raise ValueError("invalid charset alternative: %s" % type_)

        if negate:
            charset = self._negate(charset)
        return random.choice(list(charset))

    def _reverse_repeat_node(self, node_data):
        """Generates string matching 'min_repeat' or 'max_repeat' node
        from regular expression AST.

        This node matches a repetition of pattern matched by its child node.
        """
        # ``[what]`` is always a 1-element list due to quirk in ``sre_parse``;
        # for reference, see `sre_parse.py` (lines 503-514) in Python's stdlib
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
        # first value is always ``None`` due to quirk in ``sre_parse`` module;
        # for reference, see `sre_parse.py` (line 357) in Python's stdlib
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

        This node is a backreference to previously matched capture group.
        """
        # AST always refers to capture groups by index,
        # and detects circular/forward references at parse time,
        # so handling of this node can be indeed very simple
        index = node_data
        return self.groups[index]

    def _reverse_groupref_exists_node(self, node_data):
        """Generates string matching 'groupref_exists' node in regexp. AST.

        This node is a conditional test for one of the previously matched
        capture groups. Depending on whether group was matched or not,
        different subexpressions are matched next.
        """
        index, yes_pattern, no_pattern = node_data

        if self.groups[index] is not None:
            return self._reverse_nodes(yes_pattern)
        else:
            return self._reverse_nodes(no_pattern) if no_pattern else ""

    # Handling character sets

    def _charset(self, name, flags=None):
        """Return chars belonging to charset of given name.
        :param flags: Optional flags override
        """
        # FIXME: take re.LOCALE and re.UNICODE flags into account
        flags = self.flags if flags is None else flags

        if name == 'any':
            all_chars = string.printable
            if not (flags & re.DOTALL):
                all_chars = all_chars.replace("\n", "")
            return all_chars

        if name in self.BUILTIN_CHARSETS:
            return self.BUILTIN_CHARSETS[name]

        raise ValueError("invalid charset name '%s'" % name)

    def _negate(self, charset):
        """Returns negated version of given charset."""
        all_chars = self._charset('any')
        return list(set(all_chars) - set(charset))
