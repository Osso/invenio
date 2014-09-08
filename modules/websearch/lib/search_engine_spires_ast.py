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

# Abstract classes


class BinaryOp(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def accept(self, visitor):
        return visitor.visit(self, self.left.accept(visitor), self.right.accept(visitor))

    def __eq__(self, other):
        return type(self) == type(other) and self.left == other.left and self.right == other.right

    def __repr__(self):
        return "%s(%s, %s)" % (self.__class__.__name__, repr(self.left), repr(self.right))


class UnaryOp(object):
    def __init__(self, op):
        self.op = op

    def accept(self, visitor):
        return visitor.visit(self, self.op.accept(visitor))

    def __eq__(self, other):
        return type(self) == type(other) and self.op == other.op

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.op))


class Leaf(object):
    def __init__(self, value):
        self.value = value

    def accept(self, visitor):
        return visitor.visit(self)

    def __eq__(self, other):
        return type(self) == type(other) and self.value == other.value

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, repr(self.value))


# Concrete classes


class AndOp(BinaryOp):
    pass


class OrOp(BinaryOp):
    pass


class NotOp(UnaryOp):
    pass


class RangeOp(BinaryOp):
    pass


class KeywordOp(BinaryOp):
    pass


class SpiresOp(BinaryOp):
    pass


class Keyword(Leaf):
    pass


class Value(Leaf):
    pass


class SingleQuotedValue(Leaf):
    pass


class DoubleQuotedValue(Leaf):
    pass

class RegexValue(Leaf):
    pass


