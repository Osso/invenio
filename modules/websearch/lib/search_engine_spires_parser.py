# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

from pyparsing import (Word, alphas, CharsNotIn, Suppress, White, Optional,
                       Literal, quotedString, nums, Group, MatchFirst)


ignored_whitespace = Optional(Suppress(White()))

# e.g. author:S.Carli.1
field_separator = ":"

# e.g. a field like "author"
keyword = Word(alphas)

# e.g. a search patern line "S.Carli.1"
simple_value = ignored_whitespace + CharsNotIn(" \t") + ignored_whitespace

# e.g. "hello" or 'hello'
quoted_value = ('"' + CharsNotIn('"') + '*' + '"' |
                "'" + CharsNotIn("'") + '*' + "'" |
                quotedString('/') |
                quotedString('"') |
                quotedString("'"))

# e.g. 5->12
range_value = Group(Word(nums) + '->' + Word(nums))
class RangeValue(object):
    def __init__(self, results):
        self.left, dummy, self.right = list(results[0])

    def __eq__(self, other):
        return self.left == other.left and self.right == other.right

range_value.setParseAction(RangeValue)

# e.g. hello*
globbing_value = simple_value + '*'

value = quoted_value | range_value | globbing_value #| simple_value

def generate_grammar():
    return keyword + field_separator + value

GRAMMAR = generate_grammar()


def parseQuery(query, grammar=GRAMMAR):
    """Parse query string using given grammar"""
    return grammar.parseString(query, parseAll=True)
