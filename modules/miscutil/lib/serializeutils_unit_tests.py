# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Unit tests for the serialization utilities."""

import unittest
import zlib
import marshal

from invenio.testutils import make_test_suite, run_test_suite

from invenio.serializeutils import (serialize,
                                    deserialize,
                                    is_zlib_compressed)
from invenio import serializeutils


class SerializeTest(unittest.TestCase):

    if not serializeutils.LZ4_ENABLED:
        def test_data_conservation_zlib(self):
            data = 'ab'*30
            ser = serialize(data)
            self.assertTrue(is_zlib_compressed(ser))
            self.assertEqual(deserialize(ser), data)

    if serializeutils.LZ4_ENABLED:
        def test_data_conservation_lz4(self):
            data = 'ab'*30
            ser = serialize(data)
            self.assertFalse(is_zlib_compressed(ser))
            self.assertEqual(deserialize(serialize(data)), data)

    def test_fallback_to_zlib(self):
        data = 'ab'*30
        serialized_data = zlib.compress(marshal.dumps(data))
        self.assertTrue(is_zlib_compressed(serialized_data))
        self.assertEqual(deserialize(serialized_data), data)


TEST_SUITE = make_test_suite(SerializeTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
