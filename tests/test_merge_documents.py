#
# LSST Data Management System
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# See COPYRIGHT file at the top of the source tree.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <https://www.lsstcorp.org/LegalNotices/>.
#
"""Test yamlutils.merge_documents."""

from __future__ import print_function, division

import unittest
from collections import OrderedDict
from copy import deepcopy

from lsst.verify.yamlutils import merge_documents


class TestMergeDocuments(unittest.TestCase):
    """Test merge_documents, demonstrating how embedded dictionaries and
    lists are merged.
    """

    def setUp(self):
        self.base_doc = OrderedDict([
            ('A', 'a value'),
            ('B', 'b value'),
            ('C', [1, 2]),
            ('D', OrderedDict([
                ('a', 'a value'),
                ('b', 'b value'),
                ('c', OrderedDict([
                    ('alpha', 1),
                    ('beta', 3)
                ]))
            ])),
            ('E', OrderedDict(hello='world'))
        ])
        self.base_doc_copy = deepcopy(self.base_doc)

        self.new_doc = OrderedDict([
            ('B', 'over-written value'),
            ('Z', 'new value'),
            ('C', [3, 4]),
            ('D', OrderedDict([
                ('d', 'd value'),
                ('c', OrderedDict([
                    ('beta', 2),
                    ('gamma', 3)
                ]))
            ])),
            ('E', 'good-bye'),
        ])
        self.new_doc_copy = deepcopy(self.new_doc)

        self.expected = OrderedDict([
            ('A', 'a value'),
            ('B', 'over-written value'),
            ('C', [1, 2, 3, 4]),
            ('D', OrderedDict([
                ('a', 'a value'),
                ('b', 'b value'),
                ('c', OrderedDict([
                    ('alpha', 1),
                    ('beta', 2),
                    ('gamma', 3)
                ])),
                ('d', 'd value')
            ])),
            ('E', 'good-bye'),
            ('Z', 'new value'),
        ])

        self.merged = merge_documents(self.base_doc, self.new_doc)

    def test_merge(self):
        self.assertEqual(self.merged, self.expected)

    def test_immutability(self):
        """Ensure the inputs are unchanged."""
        self.assertEqual(self.base_doc, self.base_doc_copy)
        self.assertEqual(self.new_doc, self.new_doc_copy)


if __name__ == "__main__":
    unittest.main()
