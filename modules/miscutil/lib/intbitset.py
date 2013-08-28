## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

import msgpack
import zlib


MAX_INT = 1073741823


def detupling_iterator(items):
    for item in items:
        yield item[0]


class intbitset(object):

    def __init__(self, items=None, preallocate=-1, trailing_bits=0, sanity_checks=True, no_allocate=0):  # pylint: disable-msg=W0613
        # We ignore preallocate, etc.

        if isinstance(items, intbitset):
            self.trailing_bits = items.is_infinite()
            self.items = items.items.copy()
        else:
            if isinstance(items, str):
                # We assume it is a fastdump
                items, trailing_bits = self._fastload(items)
            else:
                tuple_of_tuples = items and hasattr(items, '__getitem__') and hasattr(items[0], '__getitem__')
                if tuple_of_tuples:
                    items = detupling_iterator(items)

            self.trailing_bits = trailing_bits

            if items:
                self.items = set(items)
            else:
                self.items = set()

    def __contains__(self, elem):
        if elem < 0:
            raise ValueError("Negative numbers, not allowed")
        elif elem > MAX_INT:
            raise OverflowError("Element must be <= %s" % MAX_INT)

        if elem in self.items:
            return True

        if self.trailing_bits and (not self.items or elem > max(self.items)):
            return True

        return False

    def strbits(self):
        """Return a string of 0s and 1s representing the content in memory
        of the intbitset.
        """
        if self.trailing_bits:
            raise OverflowError("It's impossible to strbits an infinite set.")
        last = 0
        ret = []
        for i in self:
            ret.append('0'*(i-last)+'1')
            last = i+1
        return ''.join(ret)

    def fastdump(self):
        obj = (list(sorted(self.items)), self.trailing_bits)
        return zlib.compress(msgpack.packb(obj))

    def fastload(self, rhs):
        items, trailing_bits = self._fastload(rhs)
        return intbitset(items, trailing_bits=trailing_bits)

    def _fastload(self, rhs):
        try:
            s = zlib.decompress(rhs)
        except zlib.error:
            raise ValueError('Invalid fastdump')
        try:
            data = msgpack.unpackb(s)
        except msgpack.UnpackValueError:
            raise ValueError('Invalid fastdump')

        return data

    def __iter__(self):
        if self.trailing_bits:
            raise OverflowError("It's impossible to iterate over an infinite set.")
        return iter(sorted(self.items))

    def __repr__(self):
        finite_list = self.extract_finite_list()
        if self.trailing_bits:
            return "intbitset(%s, trailing_bits=True)" % repr(finite_list)
        else:
            return "intbitset(%s)" % repr(finite_list)

    def extract_finite_list(self, up_to=-1):
        def generator(up_to):
            for el in self:
                if el > up_to:
                    break
                yield el

        if up_to > MAX_INT:
            raise OverflowError("up_to must be <= %s" % MAX_INT)

        if self.trailing_bits:
            return list(sorted(self.items))

        if up_to == -1:
            return list(self)
        else:
            return generator(up_to)

    def __getitem__(self, key):
        return list(self)[key]

    def is_infinite(self):
        """Return True if the intbitset is infinite. (i.e. trailing_bits=True)"""
        return self.trailing_bits

    def __isub__(self, rhs):
        if isinstance(rhs, intbitset):
            self.trailing_bits &= not rhs.is_infinite()
            if self.is_infinite():
                max_rhs = (max(rhs.items) + 1) if rhs.items else 0
                self.items |= set(self.extract_finite_list(max_rhs))
                self.items -= rhs.items
            else:
                if rhs.is_infinite():
                    max_self = self.items and max(self.items) or 0
                    self.items -= set(rhs.extract_finite_list(max_self))
                else:
                    self.items -= rhs.items
        else:
            self.items -= rhs

        return self

    def __ior__(self, rhs):
        if isinstance(rhs, intbitset):
            self.trailing_bits |= rhs.is_infinite()
            self.items |= rhs.items
        else:
            self.items |= rhs
        return self

    def __iand__(self, rhs):
        if isinstance(rhs, intbitset):
            self.trailing_bits &= rhs.is_infinite()
            self.items &= rhs.items
        else:
            self.trailing_bits = False
            self.items &= rhs
        return self

    def __ixor__(self, rhs):
        if isinstance(rhs, intbitset):
            self.trailing_bits ^= rhs.is_infinite()
            self.items ^= rhs.items
        else:
            self.items ^= rhs
        return self

    def __sub__(self, rhs):
        new = intbitset(self)
        new -= rhs
        return new

    def __and__(self, rhs):
        new = intbitset(self)
        new &= rhs
        return new

    def __or__(self, rhs):
        new = intbitset(self)
        new |= rhs
        return new

    def __xor__(self, rhs):
        new = intbitset(self)
        new ^= rhs
        return new

    def __eq__(self, rhs):
        return self.trailing_bits == rhs.trailing_bits \
                    and self.items == rhs.items

    def clear(self):
        self.trailing_bits = False
        self.items = set()

    def __ge__(self, rhs):
        return self.items >= rhs.items

    def __gt__(self, rhs):
        return self.items > rhs.items

    def __lt__(self, rhs):
        return self.items < rhs.items

    def __le__(self, rhs):
        return self.items <= rhs.items

    def __ne__(self, rhs):
        return not self == rhs

    def __nonzero__(self):
        return bool(self.items or self.trailing_bits)

    def __len__(self):
        if self.trailing_bits:
            # raise OverflowError('An infinite bitset does not have a length')
            return MAX_INT
        else:
            return len(self.items)

    def add(self, el):
        if self.trailing_bits and (not self.items or el >= max(self.items)):
            pass
        else:
            self.items.add(el)

    def remove(self, el):
        if self.trailing_bits and (not self.items or el >= max(self.items)):
            self.items = set(self.extract_finite_list(el + 1))

        self.items.remove(el)

    def discard(self, el):
        try:
            self.remove(el)
        except KeyError:
            pass

    def pop(self):
        if self.trailing_bits:
            raise KeyError('pop from an empty or infinite intbitset')
        l = list(self)
        if not l:
            raise KeyError('pop from an empty set')

        el = l.pop()
        self.items.remove(el)
        return el

    def update_with_signs(self, rhs):
        for value, sign in rhs.iteritems():
            if value < 0:
                raise ValueError("Negative numbers, not allowed")
            elif sign < 0:
                self.discard(value)
            else:
                self.add(value)
