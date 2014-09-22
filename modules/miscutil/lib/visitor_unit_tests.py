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


from invenio.testutils import (make_test_suite,
                               run_test_suite,
                               InvenioTestCase,
                               nottest)
from invenio.visitor import make_visitor


class A(object):
    pass


class B(object):
    pass


class TestVisitor(InvenioTestCase):
    visitor = make_visitor()

    @visitor(A)
    def visit(self, el):  # pylint: disable=W0613
        return 'A'

    @visitor(B)
    def visit(self, el):  # pylint: disable=W0613
        return 'B'

    def test_visit_a(self):
        self.visit(A())
        self.assertEqual(self.visit(A()), 'A')

    def test_visit_b(self):
        self.assertEqual(self.visit(B()), 'B')


TEST_SUITE = make_test_suite(TestVisitor)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
