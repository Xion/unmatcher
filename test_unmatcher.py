"""
Tests for the unmatcher module.
"""
import re

import unmatcher

import pytest


DEFAULT_TESTS_COUNT = 32
SMALL_TESTS_COUNT = 4  # used when default count would explode no. of tests

DEFAULT_CHARACTER_SETS = ('ascii_letters', 'digits')

str_arg = lambda name: {name: str, 'str_attrs': DEFAULT_CHARACTER_SETS}
str_args = lambda *names: dict([(name, str) for name in names] +
                               [('str_attrs', DEFAULT_CHARACTER_SETS)])


@pytest.mark.randomize(ncalls=DEFAULT_TESTS_COUNT, **str_arg('expr'))
def test_literal(expr):
    assert expr == unmatcher.reverse(expr)


@pytest.mark.randomize(_=int, ncalls=DEFAULT_TESTS_COUNT)
@pytest.mark.parametrize('flags', (0, re.DOTALL))
def test_any(_, flags):
    dot_re = re.compile('.', flags)
    reversed_dot = unmatcher.reverse(dot_re)
    assert bool(dot_re.match(reversed_dot))


@pytest.mark.randomize(ncalls=DEFAULT_TESTS_COUNT, **str_args('left', 'right'))
def test_branch(left, right):
    branch_re = re.compile('|'.join(map(re.escape, (left, right))))
    reversed_branch = unmatcher.reverse(branch_re)
    assert reversed_branch in (left, right)


@pytest.mark.randomize(ncalls=DEFAULT_TESTS_COUNT,
                       chars=str, str_attrs=('ascii_letters',))
def test_charset_specified(chars):
    if not chars:
        return
    charset_re = re.compile('[%s]' % chars)
    reversed_charset = unmatcher.reverse(charset_re)
    assert reversed_charset in chars


@pytest.mark.randomize(ncalls=DEFAULT_TESTS_COUNT,
                       minchar=str, maxchar=str,
                       fixed_length=1, str_attrs=('ascii_letters',))
def test_charset_range(minchar, maxchar):
    minchar, maxchar = min(minchar, maxchar), max(minchar, maxchar)
    charset_re = re.compile('[%s-%s]' % (minchar, maxchar))
    reversed_charset = unmatcher.reverse(charset_re)
    assert minchar <= reversed_charset <= maxchar


@pytest.mark.randomize(ncalls=DEFAULT_TESTS_COUNT,
                       class_=str, choices='wds')
def test_charset_class(class_):
    charset_re = re.compile(r'\%s' % class_)
    reversed_charset = unmatcher.reverse(charset_re)
    assert bool(charset_re.match(reversed_charset))


@pytest.mark.parametrize('symbol', ('+', '*'))
@pytest.mark.randomize(ncalls=DEFAULT_TESTS_COUNT,
                       fixed_length=1, **str_arg('char'))
def test_repeat_symbols(symbol, char):
    repeat_re = re.compile('%s%s' % (re.escape(char), symbol))
    reversed_repeat = unmatcher.reverse(repeat_re)
    assert bool(repeat_re.match(reversed_repeat))
    if len(reversed_repeat) == 0:
        assert symbol == '*', "empty string for repeater other than `*'"
    else:
        for chunk in chunks(reversed_repeat, len(char)):
            assert char == chunk


@pytest.mark.randomize(ncalls=SMALL_TESTS_COUNT,
                       lower_bound=int, upper_bound=int, min_num=0, max_num=4,
                       fixed_length=1, **str_arg('char'))
def test_repeat_range(lower_bound, upper_bound, char):
    if lower_bound == upper_bound:
        # test exact "range": foo{3}
        repeat_re = re.compile('%s{%d}' % (re.escape(char), lower_bound))
    elif lower_bound < upper_bound:
        # test closed range: foo{2,4}
        repeat_re = re.compile('%s{%d,%d}' % (re.escape(char),
                                              lower_bound, upper_bound))
    elif lower_bound > upper_bound:
        # test "infinite" range: foo{4,}
        lower_bound = min((lower_bound, upper_bound))
        repeat_re = re.compile('%s{%d,}' % (re.escape(char), lower_bound))
    else:
        pytest.fail()  # FSM help you if that actually happens

    reversed_repeat = unmatcher.reverse(repeat_re)
    assert bool(repeat_re.match(reversed_repeat))
    for chunk in chunks(reversed_repeat, len(char)):
        assert char == chunk


@pytest.mark.randomize(ncalls=DEFAULT_TESTS_COUNT,
                       **str_args('ingroup', 'outgroup'))
def test_noncapture_group(ingroup, outgroup):
    the_re = re.compile('(?:%s)%s' % (ingroup, outgroup))
    reversed_re = unmatcher.reverse(the_re)
    match = the_re.match(reversed_re)
    assert bool(match)
    assert len(match.groups()) == 0


@pytest.mark.randomize(ncalls=DEFAULT_TESTS_COUNT,
                       **str_args('ingroup', 'outgroup'))
def test_group_sans_backrefs(ingroup, outgroup):
    the_re = re.compile('(%s)%s' % (ingroup, outgroup))
    reversed_re = unmatcher.reverse(the_re)
    match = the_re.match(reversed_re)
    assert bool(match)
    assert match.groups() == (ingroup,)


@pytest.mark.randomize(ncalls=SMALL_TESTS_COUNT,
                       **str_args('groupname', 'ingroup', 'outgroup'))
def test_named_group_sans_backrefs(groupname, ingroup, outgroup):
    groupname = 'a' + groupname  # cannot start with digit
    the_re = re.compile('(?P<%s>%s)%s' % (groupname, ingroup, outgroup))
    reversed_re = unmatcher.reverse(the_re)
    match = the_re.match(reversed_re)
    assert bool(match)
    assert match.groupdict() == {groupname: ingroup}


@pytest.mark.randomize(ncalls=DEFAULT_TESTS_COUNT,
                       **str_args('ingroup', 'outgroup'))
def test_group_with_backrefs(ingroup, outgroup):
    the_re = re.compile(r'(%s)%s\1' % (ingroup, outgroup))
    reversed_re = unmatcher.reverse(the_re)
    match = the_re.match(reversed_re)
    assert bool(match)
    assert match.groups() == (ingroup,)


@pytest.mark.randomize(ncalls=SMALL_TESTS_COUNT,
                       **str_args('groupname', 'ingroup', 'outgroup'))
def test_named_group_with_backrefs(groupname, ingroup, outgroup):
    groupname = 'a' + groupname  # cannot start with digit
    the_re = re.compile(
        '(?P<%s>%s)%s(?P=%s)' % (groupname, ingroup, outgroup, groupname))
    reversed_re = unmatcher.reverse(the_re)
    match = the_re.match(reversed_re)
    assert bool(match)
    assert match.groupdict() == {groupname: ingroup}


@pytest.mark.randomize(ncalls=DEFAULT_TESTS_COUNT,
                       **str_args('ingroup', 'outgroup'))
def test_group_with_value(ingroup, outgroup):
    the_re = re.compile(r'(.*)%s' % outgroup)
    reversed_re = unmatcher.reverse(the_re, ingroup)
    match = the_re.match(reversed_re)
    assert bool(match)
    assert match.groups() == (ingroup,)


@pytest.mark.randomize(ncalls=SMALL_TESTS_COUNT,
                       **str_args('groupname', 'ingroup', 'outgroup'))
def test_named_group_with_value(groupname, ingroup, outgroup):
    groupname = 'a' + groupname  # cannot start with digit
    the_re = re.compile(r'(?P<%s>.*)%s' % (groupname, outgroup))
    reversed_re = unmatcher.reverse(the_re, **{groupname: ingroup})
    match = the_re.match(reversed_re)
    assert bool(match)
    assert match.groupdict() == {groupname: ingroup}


# Utility functions

def chunks(seq, n):
    """Split a ``seq``\ uence into chunks of length ``n``."""
    return (seq[i:i+n] for i in xrange(0, len(seq), n)) if len(seq) > 0 else ()
