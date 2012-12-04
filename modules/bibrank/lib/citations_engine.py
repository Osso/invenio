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
import threading
import time


from invenio.bibrank_ctation_searcher import get_citation_dict


def get_dicts(force_reload=False, dicts={}):
    if not dicts or force_reload:
        dicts['citations'] = get_citation_dict("citationdict")
        dicts['references'] = get_citation_dict("reversedict")
    return dicts


def compute_fame(citers):
    fame_info = []
    for low, high, fame in CFG_CITESUMMARY_FAME_THRESHOLDS:
        d_cites = {}
        for coll, citers in d_recid_citers.iteritems():
            d_cites[coll] = 0
            for recid, lciters in citers:
                numcites = 0
                if lciters:
                    numcites = len(lciters)
                if numcites >= low and numcites <= high:
                    d_cites[coll] += 1


def reload_dicts():
    get_dicts(force_reload=True)


class ReloadDictsThread(threading.Thread):
    def run(self):
        while True:
            time.sleep(300)
            reload_dicts()


def check_reloader_thread(status={}):
    if not status:
        status['started'] = True
        ReloadDictsThread().start()


def summarize(recids):
    check_reloader_thread()
    dicts = get_dicts()

    ret = {'breakdown': compute_fame(recids)}
    return msgpack.packb()