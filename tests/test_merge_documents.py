# See COPYRIGHT file at the top of the source tree.
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
