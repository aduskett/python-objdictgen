import sys
import re
import logging
from past.builtins import long

log = logging.getLogger('objdictgen.nosis')

# pylint: disable=invalid-name

pat_fl = r'[-+]?(((((\d+)?[.]\d+|\d+[.])|\d+)[eE][+-]?\d+)|((\d+)?[.]\d+|\d+[.]))'
re_float = re.compile(pat_fl + r'$')
re_zero = r'[+-]?0$'
pat_int = r'[-+]?[1-9]\d*'
re_int = re.compile(pat_int + r'$')
pat_flint = r'(%s|%s)' % (pat_fl, pat_int)    # float or int
re_long = re.compile(r'[-+]?\d+[lL]' + r'$')
re_hex = re.compile(r'([-+]?)(0[xX])([0-9a-fA-F]+)' + r'$')
re_oct = re.compile(r'([-+]?)(0)([0-7]+)' + r'$')
pat_complex = r'(%s)?[-+]%s[jJ]' % (pat_flint, pat_flint)
re_complex = re.compile(pat_complex + r'$')
pat_complex2 = r'(%s):(%s)' % (pat_flint, pat_flint)
re_complex2 = re.compile(pat_complex2 + r'$')


def aton(s):
    # -- massage the string slightly
    s = s.strip()
    while s[0] == '(' and s[-1] == ')':  # remove optional parens
        s = s[1:-1]

    # -- test for cases
    if re.match(re_zero, s):
        return 0

    if re.match(re_float, s):
        return float(s)

    if re.match(re_long, s):
        return long(s.rstrip('lL'))

    if re.match(re_int, s):
        return int(s)

    m = re.match(re_hex, s)
    if m:
        n = long(m.group(3), 16)
        if n < sys.maxsize:
            n = int(n)
        if m.group(1) == '-':
            n = n * (-1)
        return n

    m = re.match(re_oct, s)
    if m:
        n = long(m.group(3), 8)
        if n < sys.maxsize:
            n = int(n)
        if m.group(1) == '-':
            n = n * (-1)
        return n

    if re.match(re_complex, s):
        return complex(s)

    if re.match(re_complex2, s):
        r, i = s.split(':')
        return complex(float(r), float(i))

    raise ValueError("Invalid string '%s' passed to to_number()'d" % s)


# we use ntoa() instead of repr() to ensure we have a known output format
def ntoa(num):
    "Convert a number to a string without calling repr()"
    if isinstance(num, int):
        s = "%d" % num
    elif isinstance(num, long):
        s = "%ldL" % num
    elif isinstance(num, float):
        s = "%.17g" % num
        # ensure a '.', adding if needed (unless in scientific notation)
        if '.' not in s and 'e' not in s:
            s = s + '.'
    elif isinstance(num, complex):
        # these are always used as doubles, so it doesn't
        # matter if the '.' shows up
        s = "%.17g:%.17g" % (num.real, num.imag)
    else:
        raise ValueError("Unknown numeric type: %s" % repr(num))
    return s


def safe_string(s):
    # if isinstance(s, unicode):
    #    raise TypeError("Unicode strings may not be stored in XML attributes")

    # markup XML entities
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('"', '&quot;')
    s = s.replace("'", '&apos;')
    # for others, use Python style escapes
    s = repr(s)
    return s[1:-1]  # without the extra single-quotes


def unsafe_string(s):
    # for Python escapes, exec the string
    # (niggle w/ literalizing apostrophe)
    _s = s = s.replace("'", r"\047")
    # log.debug("EXEC in unsafe_string(): '%s'" % ("s='" + s + "'",))
    exec("s='" + s + "'")
    if s != _s:
        log.debug("EXEC in unsafe_string(): '%s' -> '%s'" % (_s, s))
    # XML entities (DOM does it for us)
    return s


def safe_content(s):
    "Markup XML entities and strings so they're XML & unicode-safe"
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')

    return s  # To be able to be used with py3

    # # wrap "regular" python strings as unicode
    # if isinstance(s, str):
    #     s = u"\xbb\xbb%s\xab\xab" % s

    # return s.encode('utf-8')


def unsafe_content(s):
    """Take the string returned by safe_content() and recreate the
    original string."""
    # don't have to "unescape" XML entities (parser does it for us)

    # # unwrap python strings from unicode wrapper
    # if s[:2] == chr(187) * 2 and s[-2:] == chr(171) * 2:
    #     s = s[2:-2].encode('us-ascii')

    return s
