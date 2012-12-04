# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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
import urllib2

from invenio.citations_engine import summarize
from invenio.config import CFG_CITATIONS_API_ADDR


def query(func, recids):
    serialized_ids = msgpack.packb(recids)
    url = "%s/%s" % (CFG_CITATIONS_API_ADDR, func)
    response = urllib2.urlopen(url, serialized_ids)
    serialized_response = response.read()
    data = msgpack.unpackb(serialized_response)
    return data


def query_summarize(recids):
    if CFG_CITATIONS_API_ADDR:
        query('summarize', recids)
    else:
        return summarize(recids)
