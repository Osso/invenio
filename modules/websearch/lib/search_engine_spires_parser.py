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

import re

from rply import ParserGenerator, LexerGenerator
# for reimporting
from rply import Token  # pylint: disable=W0611


from invenio.search_engine_spires_ast import (KeywordOp, AndOp, OrOp, NotOp,
                                              Keyword, SingleQuotedValue,
                                              DoubleQuotedValue, Value,
                                              RegexValue, RangeOp, SpiresOp)


def generate_lexer():
    lg = LexerGenerator()
    lg.add("COLON", r":")
    lg.add("FIND", re.compile(r"^\s*(find|fin|f)\b", re.I))
    lg.add("->", r"->")
    # Require whitespace before "(" parenthesis
    lg.add("(", r"\(")
    # Require whitespace after ")" parenthesis
    lg.add(")", r"\)")
    # lg.add(")", r"\)(?=\)*(\s|$))")
    lg.add("AND", re.compile(r"\band\b", re.I))
    lg.add("OR", re.compile(r"\bor\b", re.I))
    lg.add("|", r"\|")
    lg.add("<=", r"<=")
    lg.add(">=", r">=")
    lg.add(">", r">")
    lg.add("<", r"<")
    lg.add("+", r"\+")
    lg.add("AFTER", re.compile(r"\bafter\b", re.I))
    lg.add("BEFORE", re.compile(r"\bbefore\b", re.I))
    lg.add("NOT", re.compile(r"\bnot\b", re.I))
    # re to match escapes
    # r'"([^\"]|\\.)*([^\\]|\\)"'
    lg.add("SINGLE_QUOTED_STRING", r"'[^']*'")
    lg.add("DOUBLE_QUOTED_STRING", r'"[^"]*"')
    lg.add("REGEX_STRING", r"/[^/]*/")
    lg.add("*", r"\*")
    # lg.add("NUMBER", r"\b\d+\b")
    # lg.add("WORD", r"[\w\d]+(?=:|\)|\s)")
    # lg.add('KEYWORD', r'(?<=^\(*)foo')
    # lg.add('KEYWORD', r'(?<=\s)\(*)foo')
    # lg.add('KEYWORD', r'foo')
    # lg.add('-KEYWORD', r'-\s*foo')
    # lg.add("-", r"(?<=\s)-")
    lg.add("-", r"-")
    lg.add("WORD", r"[\w\d]+")
    lg.add("XWORD", r"[^\w\d\s\(\)]+")
    # lg.add("XWORD", r".+")
    lg.add('_', r"\s+")
    # lg.ignore(r"\s+")

    return lg.build()


def generate_parser(lexer, cache_id):
    pg = ParserGenerator([rule.name for rule in lexer.rules], cache_id=cache_id)

    # pylint: disable=E0102

    @pg.production("main : _? query _?")
    def rule(p):
        return p[1]

    @pg.production("main : FIND _ spires_query _?")
    def rule(p):  # pylint: disable=W0612
        return p[2]

    @pg.production("spires_query : WORD _ spires_value")
    def rule(p):  # pylint: disable=W0612
        return SpiresOp(Keyword(p[0].value), p[-1])

    @pg.production("spires_query : NOT _ spires_query")
    def rule(p):  # pylint: disable=W0612
        return NotOp(p[-1])

    @pg.production("spires_query : spires_query _ AND _ spires_query")
    def rule(p):  # pylint: disable=W0612
        return AndOp(p[0], p[-1])

    @pg.production("spires_query : spires_query _ AND")
    def rule(p):  # pylint: disable=W0612
        return SpiresOp(p[0].left, Value(p[0].right.value + p[1].value))

    @pg.production("spires_query : spires_query _ OR _ spires_query")
    def rule(p):  # pylint: disable=W0612
        return OrOp(p[0], p[-1])

    @pg.production("spires_query : spires_query _ OR")
    def rule(p):  # pylint: disable=W0612
        return SpiresOp(p[0].left, Value(p[0].right.value + p[1].value))

    @pg.production("spires_query : NOT _ spires_query")
    def rule(p):  # pylint: disable=W0612
        return NotOp(p[-1])

    @pg.production("_? : ")
    @pg.production("_? : _")
    def rule(p):  # pylint: disable=W0613
        return None

    @pg.production("spires_value : AND _ spires_value_no_op")
    @pg.production("spires_value : OR _ spires_value_no_op")
    def rule(p):  # pylint: disable=W0612
        return Value(p[0].value + p[1].value)

    @pg.production("spires_value : spires_value_no_op")
    def rule(p):  # pylint: disable=W0612
        return p[0]

    @pg.production("spires_value_no_op : AND spires_value_no_op")
    @pg.production("spires_value_no_op : OR spires_value_no_op")
    @pg.production("spires_value_no_op : spires_value_no_op AND")
    @pg.production("spires_value_no_op : spires_value_no_op OR")
    @pg.production("spires_value_no_op : spires_value_no_op AND spires_value_unit")
    @pg.production("spires_value_no_op : spires_value_no_op OR spires_value_unit")
    @pg.production("spires_value_no_op : spires_value_no_op _ spires_value_no_op")
    @pg.production("spires_value_no_op : spires_value_no_op spires_value_unit")
    def rule(p):  # pylint: disable=W0612
        return SpiresOp(Keyword(p[0].value), Value(p[-1].value))

    def rule(p):
        return Value(p[0].value + p[1].value  + p[-1].value)

    @pg.production("spires_value_no_op : spires_value_unit")
    def rule(p):
        return Value(p[0])

    @pg.production("spires_value_unit : -")
    @pg.production("spires_value_unit : WORD")
    @pg.production("spires_value_unit : XWORD")
    @pg.production("spires_value_unit : AFTER")
    @pg.production("spires_value_unit : BEFORE")
    @pg.production("spires_value_unit : NOT")
    @pg.production("spires_value_unit : |")
    @pg.production("spires_value_unit : +")
    @pg.production("spires_value_unit : *")
    @pg.production("spires_value_unit : <")
    @pg.production("spires_value_unit : <=")
    @pg.production("spires_value_unit : >")
    @pg.production("spires_value_unit : >=")
    def rule(p):  # pylint: disable=W0612
        return p[0].value

    @pg.production("isolated_query : ( _? query _? )")
    def rule(p):  # pylint: disable=W0612
        return p[1]

    @pg.production("isolated_query : _ query")
    def rule(p):
        return p[1]

    @pg.production("query : ( _? query _? )")
    def rule(p):
        return p[2]

    @pg.production("query : simple_query")
    def rule(p):
        return p[0]

    @pg.production("query : query _ AND isolated_query")
    @pg.production("query : query _ + _? query")
    @pg.production("query : query _ query")
    def rule(p):
        return AndOp(p[0], p[-1])

    @pg.production("query : query _ OR isolated_query")
    @pg.production("query : query _ | _? query")
    def rule(p):
        return OrOp(p[0], p[-1])

    @pg.production("query : NOT isolated_query")
    @pg.production("query : - _? query")
    def rule(p):
        return NotOp(p[-1])

    @pg.production("simple_query : WORD")
    def rule(p):
        return Value(p[0].value)

    @pg.production("simple_query : WORD value")
    def rule(p):
        return Value(p[0].value + p[1].value)

    @pg.production("simple_query : WORD _? COLON _? keyword_value")
    def rule(p):
        keyword = Keyword(p[0].value)
        return KeywordOp(keyword, p[-1])

    @pg.production("keyword_value : SINGLE_QUOTED_STRING")
    def rule(p):
        return SingleQuotedValue(p[0].value[1:-1])

    @pg.production("keyword_value : DOUBLE_QUOTED_STRING")
    def rule(p):
        return DoubleQuotedValue(p[0].value[1:-1])

    @pg.production("keyword_value : REGEX_STRING")
    def rule(p):
        return RegexValue(p[0].value[1:-1])

    @pg.production("keyword_value : value -> value")
    def rule(p):
        return RangeOp(p[0], p[2])

    @pg.production("keyword_value : value")
    def rule(p):
        return p[0]

    @pg.production("value_unit : -")
    @pg.production("value_unit : WORD")
    @pg.production("value_unit : XWORD")
    @pg.production("value_unit : AFTER")
    @pg.production("value_unit : BEFORE")
    @pg.production("value_unit : AND")
    @pg.production("value_unit : OR")
    @pg.production("value_unit : NOT")
    @pg.production("value_unit : |")
    @pg.production("value_unit : +")
    @pg.production("value_unit : *")
    @pg.production("value_unit : <")
    @pg.production("value_unit : <=")
    @pg.production("value_unit : >")
    @pg.production("value_unit : >=")
    def rule(p):  # pylint: disable=W0612
        return p[0].value

    @pg.production("value : value_unit")
    def rule(p):
        return Value(p[0])

    @pg.production("value : value value")
    def rule(p):
        return Value(p[0].value + p[1].value)

    @pg.production("value : ( value )")
    def rule(p):  # pylint: disable=W0612
        return Value(p[0].value + p[1].value + p[2].value)

    # pylint: enable=E0102

    @pg.error
    def error_handler(token):  # pylint: disable=W0612
        raise ValueError("Ran into a %s where it wasn't expected"
                         % token.gettokentype())

    return Parser(lexer, pg.build())


class Parser(object):
    def __init__(self, lexer, parser):
        self.lexer = lexer
        self.parser = parser

    def parse(self, query):
        tokens = list(self.lexer.lex(query))
        return self.parser.parse(iter(tokens))


LEXER = generate_lexer()
PARSER = generate_parser(LEXER, cache_id="parser")


def lexQuery(query, lexer=LEXER):
    return lexer.lex(query)


def parseQuery(query, parser=PARSER):
    """Parse query string using given grammar"""
    return parser.parse(query)
