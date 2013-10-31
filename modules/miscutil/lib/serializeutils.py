# -*- coding: utf-8 -*-
##
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

from invenio.config import CFG_COMPRESSION_FORMAT

if CFG_COMPRESSION_FORMAT == 'lz4':
    LZ4_ENABLED = True
    import lz4
else:
    LZ4_ENABLED = False

# For falback to default compression format
import zlib
import marshal


def is_zlib_compressed(data):
    return data.startswith('x\x9c')


def serialize(data, compress_only=False):
    if not compress_only:
        data = marshal.dumps(data)

    if LZ4_ENABLED:
        return lz4.compressHC(data)
    else:
        return zlib.compress(data)


def deserialize(data, decompress_only=False):
    # We try to keep the old path way fast
    # by disable the is_zlib_compressed if
    # LZ4_ENABLED is not enabled
    if not LZ4_ENABLED or is_zlib_compressed(data):
        try:
            data = zlib.decompress(data)
        except zlib.error, e:
            raise ValueError(str(e))
    else:
        try:
            data = lz4.decompress(data)
        except ValueError:
            # If the value is corrupted then we hope that marshal will
            # raise an exception anyway. Otherwise we raise the error
            # to make sure data corruption is not ignored silently
            if decompress_only:
                raise


    if decompress_only:
        return data
    else:
        return marshal.loads(data)
