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

"""CDS Invenio OAI Repository Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import sys

import invenio.oai_repository_admin as ora
from invenio.webpage import page, create_error_box
from invenio.config import CFG_SITE_URL,CFG_SITE_LANG
from invenio.dbquery import Error
from invenio.webuser import getUid, page_not_authorized
from invenio.urlutils import redirect_to_url

from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory

class WebInterfaceOaiRepositoryAdminPages(WebInterfaceDirectory):
    """Defines the set of /admin2/oairepository pages."""

    _exports = ['', 'index', 'addset', 'delset', 'editset']

    def index(self, req, form):
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']

        navtrail_previous_links = ora.getnavtrail(ln=ln)

        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Repository Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)

        auth = ora.check_user(req,'cfgoairepository')
        if not auth[0]:

            return page(title="OAI Repository Admin Interface",
                    body=ora.perform_request_index(ln),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def addset(self, req, form):
        argd = wash_urlargd(form, {'oai_set_name': (str, ""), 'oai_set_spec': (str, ""), 'oai_set_collection': (str, ""), 'oai_set_description': (str, ""), 'oai_set_definition': (str, ""), 'oai_set_reclist': (str, ""), 'oai_set_p1': (str, ""), 'oai_set_f1': (str, ""), 'oai_set_m1': (str, ""), 'oai_set_p2': (str, ""), 'oai_set_f2': (str, ""), 'oai_set_m2': (str, ""), 'oai_set_p3': (str, ""), 'oai_set_f3': (str, ""), 'oai_set_m3': (str, ""), 'oai_set_op1': (str, "a"), 'oai_set_op2': (str, "a"), 'ln': (str, "en"), 'func': (int, 0)})
        oai_set_name = argd['oai_set_name']
        oai_set_spec = argd['oai_set_spec']
        oai_set_collection = argd['oai_set_collection']
        oai_set_description = argd['oai_set_description']
        oai_set_definition = argd['oai_set_definition']
        oai_set_reclist = argd['oai_set_reclist']
        oai_set_p1 = argd['oai_set_p1']
        oai_set_f1 = argd['oai_set_f1']
        oai_set_m1 = argd['oai_set_m1']
        oai_set_p2 = argd['oai_set_p2']
        oai_set_f2 = argd['oai_set_f2']
        oai_set_m2 = argd['oai_set_m2']
        oai_set_p3 = argd['oai_set_p3']
        oai_set_f3 = argd['oai_set_f3']
        oai_set_m3 = argd['oai_set_m3']
        oai_set_op1 = argd['oai_set_op1']
        oai_set_op2 = argd['oai_set_op2']
        ln = argd['ln']
        func = argd['func']


        navtrail_previous_links = ora.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oairepository/index?ln=%s">OAI Repository Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Repository Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)

        auth = ora.check_user(req,'cfgoairepository')
        if not auth[0]:
            return page(title="Add new OAI Set",
                    body=ora.perform_request_addset(oai_set_name=oai_set_name,
                                               oai_set_spec=oai_set_spec,
                                               oai_set_collection=oai_set_collection,
                                               oai_set_description=oai_set_description,
                                               oai_set_definition=oai_set_definition,
                                               oai_set_reclist=oai_set_reclist,
                                               oai_set_p1=oai_set_p1,
                                               oai_set_f1=oai_set_f1,
                                               oai_set_m1=oai_set_m1,
                                               oai_set_p2=oai_set_p2,
                                               oai_set_f2=oai_set_f2,
                                               oai_set_m2=oai_set_m2,
                                               oai_set_p3=oai_set_p3,
                                               oai_set_f3=oai_set_f3,
                                               oai_set_m3=oai_set_m3,
                                               oai_set_op1=oai_set_op1,
                                               oai_set_op2=oai_set_op2,
                                               ln=ln,
                                               func=func),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    req=req,
                    lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def delset(self, req, form):
        argd = wash_urlargd(form, {'oai_set_id': (str, None), 'ln': (str, "en"), 'func': (int, 0)})
        oai_set_id = argd['oai_set_id']
        ln = argd['ln']
        func = argd['func']

        navtrail_previous_links = ora.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oairepository/index?ln=%s">OAI Repository Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Repository Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)

        auth = ora.check_user(req,'cfgoairepository')
        if not auth[0]:
            return page(title="Delete OAI Set",
                        body=ora.perform_request_delset(oai_set_id=oai_set_id,
                                                        ln=ln,
                                                        func=func),
                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


    def editset(self, req, form):
        argd = wash_urlargd(form, {'oai_set_id': (str, None), 'oai_set_name': (str, ""), 'oai_set_spec': (str, ""), 'oai_set_collection': (str, ""), 'oai_set_description': (str, ""), 'oai_set_definition': (str, ""), 'oai_set_reclist': (str, ""), 'oai_set_p1': (str, ""), 'oai_set_f1': (str, ""), 'oai_set_m1': (str, ""), 'oai_set_p2': (str, ""), 'oai_set_f2': (str, ""), 'oai_set_m2': (str, ""), 'oai_set_p3': (str, ""), 'oai_set_f3': (str, ""), 'oai_set_m3': (str, ""), 'oai_set_op1': (str, "a"), 'oai_set_op2': (str, "a"), 'ln': (str, "en"), 'func': (int, 0)})
        oai_set_id = argd['oai_set_id']
        oai_set_name = argd['oai_set_name']
        oai_set_spec = argd['oai_set_spec']
        oai_set_collection = argd['oai_set_collection']
        oai_set_description = argd['oai_set_description']
        oai_set_definition = argd['oai_set_definition']
        oai_set_reclist = argd['oai_set_reclist']
        oai_set_p1 = argd['oai_set_p1']
        oai_set_f1 = argd['oai_set_f1']
        oai_set_m1 = argd['oai_set_m1']
        oai_set_p2 = argd['oai_set_p2']
        oai_set_f2 = argd['oai_set_f2']
        oai_set_m2 = argd['oai_set_m2']
        oai_set_p3 = argd['oai_set_p3']
        oai_set_f3 = argd['oai_set_f3']
        oai_set_m3 = argd['oai_set_m3']
        oai_set_op1 = argd['oai_set_op1']
        oai_set_op2 = argd['oai_set_op2']
        ln = argd['ln']
        func = argd['func']


        navtrail_previous_links = ora.getnavtrail(' &gt; <a class="navtrail" href="%s/admin2/oairepository/index?ln=%s">OAI Repository Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

        try:
            uid = getUid(req)
        except Error, e:
            return page(title="OAI Repository Admin Interface - Error",
                        body=e,
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)

        auth = ora.check_user(req,'cfgoairepository')
        if not auth[0]:
            return page(title="Edit OAI Set",
                        body=ora.perform_request_editset(oai_set_id=oai_set_id,
                                                         oai_set_name=oai_set_name,
                                                         oai_set_spec=oai_set_spec,
                                                         oai_set_collection=oai_set_collection,
                                                         oai_set_description=oai_set_description,
                                                         oai_set_definition=oai_set_definition,
                                                         oai_set_reclist=oai_set_reclist,
                                                         oai_set_p1=oai_set_p1,
                                                         oai_set_f1=oai_set_f1,
                                                         oai_set_m1=oai_set_m1,
                                                         oai_set_p2=oai_set_p2,
                                                         oai_set_f2=oai_set_f2,
                                                         oai_set_m2=oai_set_m2,
                                                         oai_set_p3=oai_set_p3,
                                                         oai_set_f3=oai_set_f3,
                                                         oai_set_m3=oai_set_m3,
                                                         oai_set_op1=oai_set_op1,
                                                         oai_set_op2=oai_set_op2,
                                                         ln=ln,
                                                         func=func),

                        uid=uid,
                        language=ln,
                        req=req,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

    def __call__(self, req, form):
        """Redirect calls without final slash."""
        redirect_to_url(req, '%s/admin2/oairepository/' % CFG_SITE_URL)
