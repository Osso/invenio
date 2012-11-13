## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2010, 2011 CERN.
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

from distutils.core import setup
from distutils.extension import Extension

setup(
    name='intdict',
    version='$Revision$',
    description="""
Defines a dictionary that only stores integers and only accepts integers
as keys

Our use case is the citations counts dictionary which looks like this:
recid -> # of citations
""",
    author='Invenio developers (Alessio Deiana; last updated by $Author$)',
    author_email='info@invenio-software.org',
    url='http://invenio-software.org/',
    ext_modules=[
        Extension("invenio.intdict", ["intdict.c"], extra_compile_args=['-O3']),
    ],
)
