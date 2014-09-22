# -*- coding: utf-8 -*-

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

# pylint: disable=C0301

"""Invenio Search Engine query parsers."""

import re
import string
from invenio.dateutils import datetime

try:
    import dateutil
    if not hasattr(dateutil, '__version__') or dateutil.__version__ != '2.0':
        from dateutil import parser as du_parser
        from dateutil.relativedelta import relativedelta as du_delta
        from dateutil import relativedelta
        GOT_DATEUTIL = True
    else:
        from warnings import warn
        warn("Not using dateutil module because the version %s is not compatible with Python-2.x" % dateutil.__version__)
        GOT_DATEUTIL = False
except ImportError:
    # Ok, no date parsing is possible, but continue anyway,
    # since this package is only recommended, not mandatory.
    GOT_DATEUTIL = False

from invenio.bibindex_tokenizers.BibIndexAuthorTokenizer import BibIndexAuthorTokenizer as FNT
from invenio.logicutils import to_cnf
from invenio.config import CFG_WEBSEARCH_SPIRES_SYNTAX
from invenio.dateutils import strptime, strftime


NameScanner = FNT()


class InvenioWebSearchMismatchedParensError(Exception):
    """Exception for parse errors caused by mismatched parentheses."""
    def __init__(self, message):
        """Initialization."""
        self.message = message
    def __str__(self):
        """String representation."""
        return repr(self.message)


class SearchQueryParenthesisedParser(object):
    """Search query parser that handles arbitrarily-nested parentheses

    Parameters:
    * substitution_dict: a dictionary mapping strings to other strings.  By
      default, maps 'and', 'or' and 'not' to '+', '|', and '-'.  Dictionary
      values will be treated as valid operators for output.

    A note (valkyrie 25.03.2011):
    Based on looking through the prod search logs, it is evident that users,
    when they are using parentheses to do searches, only run word characters
    up against parens when they intend the parens to be part of the word (e.g.
    U(1)), and when they are using parentheses to combine operators, they put
    a space before and after them.  As of writing, this is the behavior that
    SQPP now expects, in order that it be able to handle such queries as
    e(+)e(-) that contain operators in parentheses that should be interpreted
    as words.
    """

    def __init__(self, substitution_dict = {'and': '+', 'or': '|', 'not': '-'}):
        self.substitution_dict = substitution_dict
        self.specials = set(['(', ')', '+', '|', '-', '+ -'])
        self.__tl_idx = 0
        self.__tl_len = 0

    # I think my names are both concise and clear
    # pylint: disable=C0103
    def _invenio_to_python_logical(self, q):
        """Translate the + and - in invenio query strings into & and ~."""
        p = q
        p = re.sub('\+ -', '&~', p)
        p = re.sub('\+', '&', p)
        p = re.sub('-', '~', p)
        p = re.sub(' ~', ' & ~', p)
        return p

    def _python_logical_to_invenio(self, q):
        """Translate the & and ~ in logical expression strings into + and -."""
        p = q
        p = re.sub('\& ~', '-', p)
        p = re.sub('~', '-', p)
        p = re.sub('\&', '+', p)
        return p
    # pylint: enable=C0103

    def parse_query(self, query):
        """Make query into something suitable for search_engine.

        This is the main entry point of the class.

        Given an expression of the form:
        "expr1 or expr2 (expr3 not (expr4 or expr5))"
        produces annoted list output suitable for consumption by search_engine,
        of the form:
        ['+', 'expr1', '|', 'expr2', '+', 'expr3 - expr4 | expr5']

        parse_query() is a wrapper for self.tokenize() and self.parse().
        """
        toklist = self.tokenize(query)
        depth, balanced, dummy_d0_p = self.nesting_depth_and_balance(toklist)
        if not balanced:
            raise SyntaxError("Mismatched parentheses in "+str(toklist))
        toklist, var_subs = self.substitute_variables(toklist)
        if depth > 1:
            toklist = self.tokenize(self.logically_reduce(toklist))
        return self.parse(toklist, var_subs)

    def substitute_variables(self, toklist):
        """Given a token list, return a copy of token list in which all free
        variables are bound with boolean variable names of the form 'pN'.
        Additionally, all the substitutable logical operators are exchanged
        for their symbolic form and implicit ands are made explicit

        e.g., ((author:'ellis, j' and title:quark) or author:stevens jones)
        becomes:
              ((p0 + p1) | p2 + p3)
        with the substitution table:
        {'p0': "author:'ellis, j'", 'p1': "title:quark",
         'p2': "author:stevens", 'p3': "jones" }

        Return value is the substituted token list and a copy of the
        substitution table.
        """
        def labels():
            i = 0
            while True:
                yield 'p'+str(i)
                i += 1

        def filter_front_ands(toklist):
            """Filter out extra logical connectives and whitespace from the front."""
            while toklist[0] == '+' or toklist[0] == '|' or toklist[0] == '':
                toklist = toklist[1:]
            return toklist

        var_subs = {}
        labeler = labels()
        new_toklist = ['']
        cannot_be_anded = self.specials.difference((')',))
        for token in toklist:
            token = token.lower()
            if token in self.substitution_dict:
                if token == 'not' and new_toklist[-1] == '+':
                    new_toklist[-1] = '-'
                else:
                    new_toklist.append(self.substitution_dict[token])
            elif token == '(':
                if new_toklist[-1] not in self.specials:
                    new_toklist.append('+')
                new_toklist.append(token)
            elif token not in self.specials:
                # apparently generators are hard for pylint to figure out
                # Turns off msg about labeler not having a 'next' method
                # pylint: disable=E1101
                label = labeler.next()
                # pylint: enable=E1101
                var_subs[label] = token
                if new_toklist[-1] not in cannot_be_anded:
                    new_toklist.append('+')
                new_toklist.append(label)
            else:
                if token == '-' and new_toklist[-1] == '+':
                    new_toklist[-1] = '-'
                else:
                    new_toklist.append(token)
        return filter_front_ands(new_toklist), var_subs

    def nesting_depth_and_balance(self, token_list):
        """Checks that parentheses are balanced and counts how deep they nest"""
        depth = 0
        maxdepth = 0
        depth0_pairs = 0
        good_depth = True
        for i in range(len(token_list)):
            token = token_list[i]
            if token == '(':
                if depth == 0:
                    depth0_pairs += 1
                depth += 1
                if depth > maxdepth:
                    maxdepth += 1
            elif token == ')':
                depth -= 1
            if depth == -1:        # can only happen with unmatched )
                good_depth = False # so force depth check to fail
                depth = 0          # but keep maxdepth in good range
        return maxdepth, depth == 0 and good_depth, depth0_pairs

    def logically_reduce(self, token_list):
        """Return token_list in conjunctive normal form as a string.

        CNF has the property that there will only ever be one level of
        parenthetical nesting, and all distributable operators (such as
        the not in -(p | q) will be fully distributed (as -p + -q).
        """

        maxdepth, dummy_balanced, d0_p = self.nesting_depth_and_balance(token_list)
        s = ' '.join(token_list)
        s = self._invenio_to_python_logical(s)
        last_maxdepth = 0
        while maxdepth != last_maxdepth:             # XXX: sometimes NaryExpr doesn't
            try:                                     # fully flatten Expr; but it usually
                s = str(to_cnf(s))                   # does in 2 passes FIXME: diagnose
            except SyntaxError:
                raise SyntaxError(str(s)+" couldn't be converted to a logic expression.")
            last_maxdepth = maxdepth
            maxdepth, dummy_balanced, d0_p = self.nesting_depth_and_balance(self.tokenize(s))
        if d0_p == 1 and s[0] == '(' and s[-1] == ')': # s can come back with extra parens
            s = s[1:-1]
        s = self._python_logical_to_invenio(s)
        return s

    def tokenize(self, query):
        """Given a query string, return a list of tokens from that string.

        * Isolates meaningful punctuation: ( ) + | -
        * Keeps single- and double-quoted strings together without interpretation.
        * Splits everything else on whitespace.

        i.e.:
        "expr1|expr2 (expr3-(expr4 or expr5))"
        becomes:
        ['expr1', '|', 'expr2', '(', 'expr3', '-', '(', 'expr4', 'or', 'expr5', ')', ')']

        special case:
        "e(+)e(-)" interprets '+' and '-' as word characters since they are in parens with
        word characters run up against them.
        it becomes:
        ['e(+)e(-)']
        """
        ###
        # Invariants:
        # * Query is never modified
        # * In every loop iteration, querytokens grows to the right
        # * The only return point is at the bottom of the function, and the only
        #   return value is querytokens
        ###

        def get_tokens(s):
            """
            Given string s, return a list of s's tokens.

            Adds space around special punctuation, then splits on whitespace.
            """
            s = ' '+s
            s = s.replace('->', '####DATE###RANGE##OP#') # XXX: Save '->'
            s = re.sub('(?P<outside>[a-zA-Z0-9_,=:]+)\((?P<inside>[a-zA-Z0-9_,+-/]*)\)',
                       '#####\g<outside>####PAREN###\g<inside>##PAREN#', s) # XXX: Save U(1) and SL(2,Z)
            s = re.sub('####PAREN###(?P<content0>[.0-9/-]*)(?P<plus>[+])(?P<content1>[.0-9/-]*)##PAREN#',
                       '####PAREN###\g<content0>##PLUS##\g<content1>##PAREN#', s)
            s = re.sub('####PAREN###(?P<content0>([.0-9/]|##PLUS##)*)(?P<minus>[-])' +\
                                   '(?P<content1>([.0-9/]|##PLUS##)*)##PAREN#',
                       '####PAREN###\g<content0>##MINUS##\g<content1>##PAREN#', s) # XXX: Save e(+)e(-)
            for char in self.specials:
                if char == '-':
                    s = s.replace(' -', ' - ')
                    s = s.replace(')-', ') - ')
                    s = s.replace('-(', ' - (')
                else:
                    s = s.replace(char, ' '+char+' ')
            s = re.sub('##PLUS##', '+', s)
            s = re.sub('##MINUS##', '-', s) # XXX: Restore e(+)e(-)
            s = re.sub('#####(?P<outside>[a-zA-Z0-9_,=:]+)####PAREN###(?P<inside>[a-zA-Z0-9_,+-/]*)##PAREN#',
                       '\g<outside>(\g<inside>)', s) # XXX: Restore U(1) and SL(2,Z)
            s = s.replace('####DATE###RANGE##OP#', '->') # XXX: Restore '->'
            return s.split()

        querytokens = []
        current_position = 0

        re_quotes_match = re.compile(r'(?![\\])(".*?[^\\]")' + r"|(?![\\])('.*?[^\\]')")

        for match in re_quotes_match.finditer(query):
            match_start = match.start()
            quoted_region = match.group(0).strip()

            # clean the content after the previous quotes and before current quotes
            unquoted = query[current_position : match_start]
            querytokens.extend(get_tokens(unquoted))

            # XXX: In case we end up with e.g. title:, "compton scattering", make it
            # title:"compton scattering"
            if querytokens and querytokens[0] and querytokens[-1][-1] == ':':
                querytokens[-1] += quoted_region
            # XXX: In case we end up with e.g. "expr1",->,"expr2", make it
            # "expr1"->"expr2"
            elif len(querytokens) >= 2 and querytokens[-1] == '->':
                arrow = querytokens.pop()
                querytokens[-1] += arrow + quoted_region
            else:
                # add our newly tokenized content to the token list
                querytokens.extend([quoted_region])

            # move current position to the end of the tokenized content
            current_position = match.end()

        # get tokens from the last appearance of quotes until the query end
        unquoted = query[current_position : len(query)]
        querytokens.extend(get_tokens(unquoted))

        return querytokens

    def parse(self, token_list, variable_substitution_dict=None):
        """Make token_list consumable by search_engine.

        Turns a list of tokens and a variable mapping into a grouped list
        of subexpressions in the format suitable for use by search_engine,
        e.g.:
        ['+', 'searchterm', '-', 'searchterm to exclude', '|', 'another term']

        Incidentally, this works recursively so parens can cause arbitrarily
        deep nestings.  But since the search_engine doesn't know about nested
        structures, we need to flatten the input structure first.
        """
        ###
        # Invariants:
        # * Token list is never modified
        # * Balanced parens remain balanced; unbalanced parens are an error
        # * Individual tokens may only be exchanged for items in the variable
        #   substitution dict; otherwise they pass through unmolested
        # * Return value is built up mostly as a stack
        ###

        op_symbols = self.substitution_dict.values()
        self.__tl_idx = 0
        self.__tl_len = len(token_list)

        def inner_parse(token_list, open_parens=False):
            '''
                although it's not in the API, it seems sensible to comment
                this function a bit.

                dist_token here is a token (e.g. a second-order operator)
                which needs to be distributed across other tokens inside
                the inner parens
            '''

            if open_parens:
                parsed_values = []
            else:
                parsed_values = ['+']

            i = 0
            while i < len(token_list):
                token = token_list[i]
                if i > 0 and parsed_values[-1] not in op_symbols:
                    parsed_values.append('+')
                if token == '(':
                    # if we need to distribute something over the tokens inside the parens
                    # we will know it because... it will end in a :
                    # that part of the list will be 'px', '+', '('
                    distributing = (len(parsed_values) > 2 and parsed_values[-2].endswith(':') and parsed_values[-1] == '+')
                    if distributing:
                        # we don't need the + if we are distributing
                        parsed_values = parsed_values[:-1]
                    offset = self.__tl_len - len(token_list)
                    inner_value = inner_parse(token_list[i+1:], True)
                    inner_value = ' '.join(inner_value)
                    if distributing:
                        if len(self.tokenize(inner_value)) == 1:
                            parsed_values[-1] = parsed_values[-1] + inner_value
                        elif "'" in inner_value:
                            parsed_values[-1] = parsed_values[-1] + '"' + inner_value + '"'
                        elif '"' in inner_value:
                            parsed_values[-1] = parsed_values[-1] + "'" + inner_value + "'"
                        else:
                            parsed_values[-1] = parsed_values[-1] + '"' + inner_value + '"'
                    else:
                        parsed_values.append(inner_value)
                    self.__tl_idx += 1
                    i = self.__tl_idx - offset
                elif token == ')':
                    if parsed_values[-1] in op_symbols:
                        parsed_values = parsed_values[:-1]
                    if len(parsed_values) > 1 and parsed_values[0] == '+' and parsed_values[1] in op_symbols:
                        parsed_values = parsed_values[1:]
                    return parsed_values
                elif token in op_symbols:
                    if len(parsed_values) > 0:
                        parsed_values[-1] = token
                    else:
                        parsed_values = [token]
                else:
                    if variable_substitution_dict != None and token in variable_substitution_dict:
                        token = variable_substitution_dict[token]
                    parsed_values.append(token)
                i += 1
                self.__tl_idx += 1

            # If we have an extra start symbol, remove the default one
            if parsed_values[1] in op_symbols:
                parsed_values = parsed_values[1:]
            return parsed_values

        return inner_parse(token_list, False)
