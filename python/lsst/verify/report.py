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
from __future__ import print_function, division

__all__ = ['Report']

from astropy.table import Table

from .naming import Name


class Report(object):
    """Report tabulating specification pass/fail status for a set of
    `lsst.verify.Measurement`\ s.

    Parameters
    ----------
    measurements : `lsst.verify.MeasurementSet`
        Measurements to be tested.
    specs : `lsst.verify.SpecificationSet`
        Specifications to test measurements against. These specifications
        are assumed to be relevant to the measurements. Use
        `lsst.verify.SpecificationSet.subset`, passing in job metadata
        (`lsst.verify.Job.meta`), to ensure this.
    """

    def __init__(self, measurements, specs):
        self._meas_set = measurements
        self._spec_set = specs

    def make_table(self):
        """Make an table summarizing specification tests of measurements.

        Returns
        -------
        table : `astropy.table.Table`
            Table with columns:

            - **Status**
            - **Specification**
            - **Measurement**
            - **Test**
            - **Metric Tags**
            - **Spec. Tags**
        """
        # Columns for the table
        statuses = []
        spec_name_items = []
        measurements = []
        tests = []
        metric_tags = []
        spec_tags = []

        spec_names = list(self._spec_set.keys())
        spec_names.sort()

        for spec_name in spec_names:
            # Test if there is a measurement for this specification,
            # if not, we just skip it.
            metric_name = Name(package=spec_name.package,
                               metric=spec_name.metric)
            try:
                meas = self._meas_set[metric_name]
            except KeyError:
                # No measurement for this specification, just skip it.
                continue

            spec = self._spec_set[spec_name]

            if spec.check(meas.quantity):
                # Passed
                # http://emojipedia.org/white-heavy-check-mark/
                statuses.append(u'\U00002705')
            else:
                # Failed.
                # http://emojipedia.org/cross-mark/
                statuses.append(u'\U0000274C')

            spec_name_items.append(str(spec_name))

            measurements.append(meas._repr_latex_())

            tests.append(spec._repr_latex_())

            tags = list(spec.tags)
            tags.sort()
            spec_tags.append(', '.join(tags))

            metric = meas.metric
            if metric is None:
                # no metric is available, this is the default
                metric_tags.append('N/A')
            else:
                tags = list(metric.tags)
                tags.sort()
                metric_tags.append(', '.join(tags))

        table = Table([statuses, spec_name_items, measurements, tests,
                       metric_tags, spec_tags],
                      names=['Status', 'Specification', 'Measurement', 'Test',
                             'Metric Tags', 'Spec. Tags'])
        return table

    def _repr_html_(self):
        """HTML representation of the report for Jupyter notebooks."""
        table = self.make_table()
        return table._repr_html_()

    def show(self):
        """Display the report in a Jupyter notebook."""
        table = self.make_table()
        return table.show_in_notebook(show_row_index='')
