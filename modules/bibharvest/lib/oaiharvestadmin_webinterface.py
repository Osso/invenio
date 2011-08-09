## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CDS Invenio OAI Harvest Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import invenio.oai_harvest_admin as oha
import simplejson as json
import datetime
import math
import urllib
from invenio.webpage import page, create_error_box
from invenio.config import CFG_SITE_NAME, CFG_SITE_URL, CFG_SITE_LANG
from invenio.dbquery import Error
from invenio.webuser import getUid, page_not_authorized
from invenio.bibrankadminlib import check_user
from invenio.oai_harvest_dblayer import get_holdingpen_day_size
from invenio.urlutils import redirect_to_url

from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory

class WebInterfaceOaiHarvestAdminPages(WebInterfaceDirectory):
    """Defines the set of /admin2/oaiharvest pages."""

    _exports = ['', 'index', 'editsource', 'addsource', 'delsource', 'testsource', 'viewhistory', 'viewhistoryday', 'viewentryhistory', 'viewtasklogs', 'viewhprecord', 'accepthprecord', 'delhprecord', 'reharvest', 'harvest', 'preview_original_xml', 'preview_harvested_xml', 'getHoldingPenData', 'get_entries_fragment', 'viewholdingpen']

    def index(self, req, form):
        """Main OAI Harvest admin page"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        navtrail_previous_links = oha.getnavtrail(ln=ln)

        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)

        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            return page(title="OAI Harvest Admin Interface",
                        body=oha.perform_request_index(ln),
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def editsource(self, req, form):
        argd = wash_urlargd(form, {'oai_src_id': (str, None), 'oai_src_name': (str, ""), 'oai_src_baseurl': (str, ""), 'oai_src_prefix': (str, ""), 'oai_src_frequency': (str, ""), 'oai_src_config': (str, ""), 'oai_src_post': (str, ""), 'ln': (str, "en"), 'mtype': (str, ""), 'callback': (str, "yes"), 'confirm': (int, -1), 'oai_src_sets': (list, None), 'oai_src_bibfilter': (str, "")})
        oai_src_id = argd['oai_src_id']
        oai_src_name = argd['oai_src_name']
        oai_src_baseurl = argd['oai_src_baseurl']
        oai_src_prefix = argd['oai_src_prefix']
        oai_src_frequency = argd['oai_src_frequency']
        oai_src_config = argd['oai_src_config']
        oai_src_post = argd['oai_src_post']
        ln = argd['ln']
        mtype = argd['mtype']
        callback = argd['callback']
        confirm = argd['confirm']
        oai_src_sets = argd['oai_src_sets']
        if oai_src_sets == None:
            oai_src_sets = []
        oai_src_bibfilter = argd['oai_src_bibfilter']

        navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oaiharvest/index?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)

        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            if isinstance(oai_src_sets, str):
                oai_src_sets = [oai_src_sets]
            return page(title="Edit OAI Source",
                        body=oha.perform_request_editsource(oai_src_id=oai_src_id,
                                                            oai_src_name=oai_src_name,
                                                            oai_src_baseurl=oai_src_baseurl,
                                                            oai_src_prefix=oai_src_prefix,
                                                            oai_src_frequency=oai_src_frequency,
                                                            oai_src_config=oai_src_config,
                                                            oai_src_post=oai_src_post,
                                                            oai_src_sets=oai_src_sets,
                                                            oai_src_bibfilter=oai_src_bibfilter,
                                                            ln=ln,
                                                            confirm=confirm),
                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def addsource(self, req, form):
        argd = wash_urlargd(form, {'ln': (str, "en"), 'oai_src_name': (str, ""), 'oai_src_baseurl': (str, ""), 'oai_src_prefix': (str, ""), 'oai_src_frequency': (str, ""), 'oai_src_lastrun': (str, ""), 'oai_src_config': (str, ""), 'oai_src_post': (str, ""), 'confirm': (int, -1), 'oai_src_sets': (list, None), 'oai_src_bibfilter': (str, "")})
        ln = argd['ln']
        oai_src_name = argd['oai_src_name']
        oai_src_baseurl = argd['oai_src_baseurl']
        oai_src_prefix = argd['oai_src_prefix']
        oai_src_frequency = argd['oai_src_frequency']
        oai_src_lastrun = argd['oai_src_lastrun']
        oai_src_config = argd['oai_src_config']
        oai_src_post = argd['oai_src_post']
        confirm = argd['confirm']
        oai_src_sets = argd['oai_src_sets']
        if oai_src_sets == None:
            oai_src_sets = []
        oai_src_bibfilter = argd['oai_src_bibfilter']

        navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oaiharvest/index?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)

        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            if isinstance(oai_src_sets, str):
                oai_src_sets = [oai_src_sets]
            return page(title="Add new OAI Source",
                        body=oha.perform_request_addsource(oai_src_name=oai_src_name,
                                                           oai_src_baseurl=oai_src_baseurl,
                                                           oai_src_prefix=oai_src_prefix,
                                                           oai_src_frequency=oai_src_frequency,
                                                           oai_src_lastrun=oai_src_lastrun,
                                                           oai_src_config=oai_src_config,
                                                           oai_src_post=oai_src_post,
                                                           oai_src_sets=oai_src_sets,
                                                           oai_src_bibfilter=oai_src_bibfilter,
                                                           ln=ln,
                                                           confirm=confirm),
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        req=req,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def delsource(self, req, form):
        argd = wash_urlargd(form, {'oai_src_id': (str, None), 'ln': (str, "en"), 'confirm': (int, 0)})
        oai_src_id = argd['oai_src_id']
        ln = argd['ln']
        confirm = argd['confirm']

        navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oaiharvest/index?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)

        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            return page(title="Delete OAI Source",
                        body=oha.perform_request_delsource(oai_src_id=oai_src_id,
                                                        ln=ln,
                                                        confirm=confirm),
                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def testsource(self, req, form):
        argd = wash_urlargd(form, {'oai_src_id': (str, None), 'ln': (str, "en"), 'confirm': (str, 0), 'record_id': (str, None)})
        oai_src_id = argd['oai_src_id']
        ln = argd['ln']
        confirm = argd['confirm']
        record_id = argd['record_id']

        navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oaiharvest/index?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            return page(title="Test OAI Source",
                        body=oha.perform_request_testsource(oai_src_id=oai_src_id,
                                                            ln=ln,
                                                            confirm=confirm,
                                                            record_id=record_id),
                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def viewhistory(self, req, form):
        argd = wash_urlargd(form, {'oai_src_id': (str, 0), 'ln': (str, "en"), 'confirm': (str, 0), 'year': (str, None), 'month': (str, None)})
        oai_src_id = argd['oai_src_id']
        ln = argd['ln']
        confirm = argd['confirm']
        year = argd['year']
        month = argd['month']

        navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oaiharvest/index?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
        d_date = datetime.datetime.now()
        if year == None:
            year = d_date.year
        if month == None:
            month = d_date.month
        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            return page(title="View OAI source harvesting history",
                        body=oha.perform_request_viewhistory(oai_src_id=oai_src_id,
                                                        ln=ln,
                                                        confirm=confirm,
                                                        year = int(year),
                                                        month = int(month)),
                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def viewhistoryday(self, req, form):
        argd = wash_urlargd(form, {'oai_src_id': (str, 0), 'ln': (str, "en"), 'confirm': (str, 0), 'year': (str, None), 'month': (str, None), 'day': (str, None), 'start': (int, 0)})
        oai_src_id = argd['oai_src_id']
        ln = argd['ln']
        confirm = argd['confirm']
        year = argd['year']
        month = argd['month']
        day = argd['day']
        start = argd['start']

        navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oaiharvest/index?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
        d_date = datetime.datetime.now()
        if year == None:
            year = d_date.year
        if month == None:
            month = d_date.month
        if day == None:
            day = d_date.day
        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            return page(title="View OAI source harvesting history",
                        body=oha.perform_request_viewhistoryday(oai_src_id=oai_src_id,
                                                        ln=ln,
                                                        confirm=confirm,
                                                        year = int(year),
                                                        month = int(month),
                                                        day = int(day),
                                                        start = int(start)),
                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def viewentryhistory(self, req, form):
        argd = wash_urlargd(form, {'oai_id': (str, 0), 'ln': (str, "en"), 'confirm': (str, 0), 'start': (int, 0)})
        oai_id = argd['oai_id']
        ln = argd['ln']
        confirm = argd['confirm']
        start = argd['start']

        navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oaiharvest/index?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            return page(title="View OAI source harvesting history (single record)",
                        body=oha.perform_request_viewentryhistory(oai_id = str(oai_id),
                                                        ln=ln,
                                                        confirm=confirm,
                                                        start = int(start)),
                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def viewtasklogs(self, req, form):
        argd = wash_urlargd(form, {'ln': (str, "en"), 'confirm': (str, 0), 'task_id': (int, 0)})
        ln = argd['ln']
        confirm = argd['confirm']
        task_id = argd['task_id']

        navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oaiharvest/index?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            return page(title="View bibsched task logs",
                        body=oha.perform_request_viewtasklogs(ln=ln,
                                                        confirm=confirm,
                                                        task_id = int(task_id)),
                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def viewhprecord(self, req, form):
        argd = wash_urlargd(form, {'ln': (str, "en"), 'confirm': (str, 0), 'hpupdate_id': (int, 0)})
        ln = argd['ln']
        confirm = argd['confirm']
        hpupdate_id = argd['hpupdate_id']

        navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oaiharvest/index?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            return page(title="Holding Pen Record",
                        body=oha.perform_request_viewhprecord(hpupdate_id = hpupdate_id,
                                                              ln=ln,
                                                              confirm=confirm),
                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def accepthprecord(self, req, form):
        argd = wash_urlargd(form, {'ln': (str, "en"), 'confirm': (str, 0), 'hpupdate_id': (int, 0)})
        ln = argd['ln']
        confirm = argd['confirm']
        hpupdate_id = argd['hpupdate_id']

        navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oaiharvest/index?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            return page(title="Holding Pen Record",
                        metaheaderadd = oha.view_holdingpen_headers(),
                        body=oha.perform_request_accepthprecord(hpupdate_id = hpupdate_id,
                                                              ln=ln,
                                                              confirm=confirm),
                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def delhprecord(self, req, form):
        argd = wash_urlargd(form, {'ln': (str, "en"), 'confirm': (str, 0), 'task_id': (str, 0), 'hpupdate_id': (int, 0)})
        ln = argd['ln']
        confirm = argd['confirm']
        task_id = argd['task_id']
        hpupdate_id = argd['hpupdate_id']

        navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oaiharvest/index?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            return page(title="Holding Pen Record",
                        body=oha.perform_request_delhprecord(hpupdate_id = hpupdate_id,
                                                                ln=ln,
                                                                confirm=confirm),
                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def reharvest(self, req, form):
        argd = wash_urlargd(form, {'oai_src_id': (str, None), 'ln': (str, "en"), 'confirm': (int, 0), 'records': (dict, {}) })
        oai_src_id = argd['oai_src_id']
        ln = argd['ln']
        confirm = argd['confirm']
        records = argd['records']

        navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oaiharvest/index?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            return page(title="OAI source - reharvesting records",
                        body=oha.perform_request_reharvest_records(oai_src_id=oai_src_id,
                                                        ln=ln,
                                                        confirm=confirm, record_ids = records),
                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def harvest(self, req, form):
        argd = wash_urlargd(form, {'oai_src_id': (str, None), 'ln': (str, "en"), 'confirm': (str, 0), 'record_id': (str, None)})
        oai_src_id = argd['oai_src_id']
        ln = argd['ln']
        confirm = argd['confirm']
        record_id = argd['record_id']

        navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oaiharvest/index?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            return page(title="OAI source - harvesting new records",
                        body=oha.perform_request_harvest_record(oai_src_id = oai_src_id,
                                                        ln=ln,
                                                        confirm=confirm, record_id = record_id),
                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def preview_original_xml(self, req, form):
        argd = wash_urlargd(form, {'oai_src_id': (str, None), 'ln': (str, "en"), 'record_id': (str, None)})
        oai_src_id = argd['oai_src_id']
        ln = argd['ln']
        record_id = argd['record_id']

        navtrail_previous_links =oha.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin2/oaiharvest">OAI Harvest Admin Interface</a> """ % (CFG_SITE_URL)
        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            if (record_id == None) or (oai_src_id == None):
                req.content_type = "text/plain";
                req.write("No record number provided")
                return
            req.content_type = "text/xml"
            return oha.perform_request_preview_original_xml(oai_src_id, record_id)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def preview_harvested_xml(self, req, form):
        argd = wash_urlargd(form, {'oai_src_id': (str, None), 'ln': (str, "en"), 'record_id': (str, None)})
        oai_src_id = argd['oai_src_id']
        ln = argd['ln']
        record_id = argd['record_id']

        navtrail_previous_links = oha.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin2/oaiharvest">OAI Harvest Admin Interface</a> """ % (CFG_SITE_URL)
        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Harvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        auth = check_user(req,'cfgoaiharvest')
        if not auth[0]:
            if (record_id == None) or (oai_src_id == None):
                req.content_type = "text/plain";
                req.write("No record number provided")
                return
            content = oha.perform_request_preview_harvested_xml(oai_src_id, record_id)
            if content[0]:
                req.content_type = "text/xml"
            else:
                req.content_type = "text/plain"
            return content[1]
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def getHoldingPenData(self, req, form):
        argd = wash_urlargd(form, {'elementId': (str, 0)})
        elementId = argd['elementId']

        try:
            uid = getUid(req)
        except Error, e:
            return "unauthorised access !"
        auth = check_user(req,'cfgoaiharvest')
        if auth[0]:
            return "unauthorised access !"

        elements = elementId.split("_")
        prefix = elements[0]
        resultHtml = None
        additionalData = None

        if len(elements) == 2:
            filter = elements[1]
            resultHtml =  oha.perform_request_gethpyears(elements[0], filer);
        elif len(elements) == 3:
            # only the year is specified
            result = ""
            filter = elements[2]
            nodeYear = int(elements[1])
            resultHtml = oha.perform_request_gethpyear(elements[0], nodeYear, filter)

        elif len(elements) == 4:
            # year and month specified
            nodeYear = int(elements[1])
            nodeMonth = int(elements[2])
            filter = elements[3]
            resultHtml = oha.perform_request_gethpmonth(elements[0], nodeYear, nodeMonth, filter)

        elif len(elements) == 5:
            # year, month and day specified - returning the entries themselves
            nodeYear = int(elements[1])
            nodeMonth = int(elements[2])
            nodeDay = int(elements[3])
            filter = elements[4]
            daySize = get_holdingpen_day_size(nodeYear, nodeMonth, nodeDay, filter);
            resultHtml = """<li><div id="%s_pager"></div>&nbsp;</li>""" %(elementId,)
            resultsPerPage = 20
            numberOfPages = math.ceil(float(daySize) / resultsPerPage)
            pages = []
            urlFilter = urllib.quote(filter)
            for i in range(0, numberOfPages):
                pages += [
                {
                "url": "%s/admin2/oaiharvest/get_entries_fragment?year=%s&month=%s&day=%s&start=%i&limit=%i&filter=%s" % (CFG_SITE_URL, nodeYear, nodeMonth, nodeDay, i * resultsPerPage, resultsPerPage, urlFilter),
                "selector": False,
                "type": "ajax",
                }]

            additionalData = {
                   "pagerId": elementId + "_pager",
                   "pages" : pages
               }
        else:
            # nothing of the above. error
            resultHtml = "Wrong request"

        return json.dumps({"elementId": elementId, "html" : resultHtml, "additionalData" : additionalData})


    def get_entries_fragment(self, req, form):
        argd = wash_urlargd(form, {'year': (int, 0), 'month': (int, 0), 'day': (int, 0), 'start': (int, 0), 'limit': (int, 0), 'filter': (int, 0)})
        year = argd['year']
        month = argd['month']
        day = argd['day']
        start = argd['start']
        limit = argd['limit']
        filter = argd['filter']

        try:
            uid = getUid(req)
        except Error, e:
            return "unauthorised access !"
        auth = check_user(req, 'cfgoaiharvest')
        if not auth[0]:
            return oha.perform_request_gethpdayfragment(int(year), int(month), int(day), int(limit), int(start), filter)
        else:
            return "unauthorised access !"


    def viewholdingpen(self, req, form):
        argd = wash_urlargd(form, {'filter': (str, ""), 'ln': (str, "en")})
        filter = argd['filter']
        ln = argd['ln']

        navtrail_previous_links = oha.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin2/oaiharvest">BibHarvest Admin Interface</a> """ % (CFG_SITE_URL)
        try:
            uid = getUid(req)
        except Error, e:
            return page(title="BibHarvest Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)
        auth = check_user(req, 'cfgoaiharvest')
        if not auth[0]:
            return page(title="Holding Pen",
                        metaheaderadd = oha.view_holdingpen_headers(),
                        body = oha.perform_request_view_holdingpen_tree(filter),
                        uid = uid,
                        language = ln,
                        req = req,
                        navtrail = navtrail_previous_links,
                        lastupdated = __lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

    def __call__(self, req, form):
        """Redirect calls without final slash."""
        redirect_to_url(req, '%s/admin2/oaiharvest/' % CFG_SITE_URL)
