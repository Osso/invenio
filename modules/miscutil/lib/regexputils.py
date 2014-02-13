# -*- coding:utf-8 -*-
##
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
"""Serialization an deserialization of regular expressions"""


import sre_compile
import sre_parse
import _sre
import cPickle as pickle


# the first half of sre_compile.compile
def raw_compile(p, flags=0):
    # internal: convert pattern list to internal format
    if sre_compile.isstring(p):
        p = sre_parse.parse(p, flags)

    code = sre_compile._code(p, flags)

    return p, code

# the second half of sre_compile.compile
def build_compiled(pattern, flags, p, code):
    # map in either direction
    groupindex = p.pattern.groupdict
    indexgroup = [None] * p.pattern.groups
    for k, i in groupindex.iteritems():
        indexgroup[i] = k

    return _sre.compile(
        pattern, flags | p.pattern.flags, code,
        p.pattern.groups-1,
        groupindex, indexgroup
        )


def prepare_regexp(pattern, flags):
    p, code = raw_compile(pattern, flags)
    return (pattern, flags, p, code)


def compile_regexp(fragments):
    return build_compiled(*fragments)


def pickle_regexps(regexes):
    picklable = [prepare_regexp(pattern, flags) for pattern, flags in regexes]
    return pickle.dumps(picklable)


def unpickle_regexps(serialized_regexps):
    regexps = []
    for pattern, flags, p, code in pickle.loads(serialized_regexps):
        regexps.append(build_compiled(pattern, flags, p, code))
    return regexps
