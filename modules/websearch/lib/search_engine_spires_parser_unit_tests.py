# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2010, 2011, 2012, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Unit tests for the search engine query parsers."""

from pyparsing import ParseResults


from invenio.testutils import (make_test_suite,
                               run_test_suite,
                               InvenioTestCase,
                               nottest)
from invenio.search_engine_spires_parser import (parseQuery,
                                                 RangeValue)


@nottest
def generate_query_test(query, expected):
    def func(self):
        output = parseQuery(query)
        self.assertEqual(output.asList(), expected)
    return func


@nottest
def generate_tests(cls):
    for count, (query, expected) in enumerate(cls.queries):
        func = generate_query_test(query, expected)
        func.__name__ = 'test_%s' % count
        func.__doc__ = "Parsing query %s" % query
        setattr(cls, func.__name__, func)
    return cls


@generate_tests  # pylint: disable=R0903
class TestBasicParser(InvenioTestCase):
    """Test utility functions for the parsing components"""

    queries = (
        ("foo:bar", ['foo', ':', 'bar']),
        ("foo: bar", ['foo', ':', 'bar']),
        ("foo: 'bar'", ['foo', ':', "'bar'"]),
        ("foo: \"bar\"", ['foo', ':', '"bar"']),
        ("foo: /bar/", ['foo', ':', '/bar/']),
        ("foo: \"'bar'\"", ['foo', ':', "\"'bar'\""]),
        ("year: 2000->2012", ['year', ':', RangeValue([['2000', '->', '2012']])]),
        ("foo: hello*", ['foo', ':', 'hello', '*']),
        # ("foo: 'hello*'", ['foo', ':', 'hello', '*']),
        # ("foo: \"hello*\"", ['foo', ':', 'hello', '*']),
        ("foo: he*o", ['foo', ':', 'he*o']),
    )
    queries = (
        # ("foo: hello*", ['foo', ':', 'hello', '*']),
        ("foo: 'hello*'", ['foo', ':', 'hello', '*']),
    )

TEST_SUITE = make_test_suite(TestBasicParser)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
