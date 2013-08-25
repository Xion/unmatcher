"""
Tests for the unmatcher module.
"""
import re

import unmatcher

import pytest


DEFAULT_TESTS_COUNT = 256

str_arg = lambda name: {name: str, 'str_attrs': ('ascii_letters', 'digits')}


@pytest.mark.randomize(ncalls=DEFAULT_TESTS_COUNT, **str_arg('expr'))
def test_literal(expr):
    assert expr == unmatcher.reverse(expr)


@pytest.mark.randomize(_=int, ncalls=DEFAULT_TESTS_COUNT)
@pytest.mark.parametrize('flags', (0, re.DOTALL))
def test_any(_, flags):
    dot_re = re.compile('.', flags)
    reversed_dot = unmatcher.reverse(dot_re)
    assert bool(dot_re.match(reversed_dot))


# TODO: test charset ranges: [abc], [a-z], \d
# TODO: test branching: a|b, a|b|c, a|b|\d, etc.


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


# NOTE: total number of test cases here is ncalls * (max_num - min_num) ** 2
#       so be careful if not setting the parameters too high
@pytest.mark.randomize(ncalls=4,
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


# TODO: test repeat range without upper_bound: foo{2}, bar{7}, etc.

# TODO: test non-capture groups: (?:foo)bar
# TODO: test capture groups without backreferences: (foo)bar, (?P<huh>foo)bar
# TODO: test capture groups with backreferences: (foo)bar\1, (?P<huh>foo)bar(?P=huh)


# Utility functions

def chunks(seq, n):
    """Split a ``seq``\ uence into chunks of length ``n``."""
    return (seq[i:i+n] for i in xrange(0, len(seq), n)) if len(seq) > 0 else ()
