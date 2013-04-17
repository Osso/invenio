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

from datetime import datetime, timedelta

from invenio.bibtask import task_init
from invenio.dbquery import run_sql


def task_run_core():
    timecut = datetime.now() - timedelta(hours=60)
    rows = run_sql('SELECT name, last_updated FROM idxINDEX')
    for name, last_updated in rows:
        if last_updated < timecut:
            raise Exception('Index %s was last updated on %s' % (name, last_updated))
    return True


def main():
    """Main that construct all the bibtask."""
    task_init(authorization_action='runbibindex',
              authorization_msg="BibIndex Checker Task Submission",
              description="",
              version="1.0",
              task_run_fnc=task_run_core)


if __name__ == '__main__':
    main()
