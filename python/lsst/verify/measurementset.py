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

__all__ = ['MeasurementSet']

from .measurement import Measurement
from .naming import Name
from .jsonmixin import JsonSerializationMixin


class MeasurementSet(JsonSerializationMixin):
    r"""A collection of `~lsst.verify.Measurement`\ s of
    `~lsst.verify.Metric`\ s.

    ``MeasurementSet`` provides a dict-like interface for getting, setting,
    and iterating over `Measurement`\ s.

    Parameters
    ----------
    measurements : `list` of `lsst.verify.Measurement`\ s
        Measurements to include in the set.
    """

    def __init__(self, measurements=None):
        self._items = {}
        if measurements is not None:
            for measurement in measurements:
                self[measurement.metric_name] = measurement

    @classmethod
    def deserialize(cls, measurements=None, blob_set=None, metric_set=None):
        """Create a measurement set from a parsed JSON dataset.

        Parameters
        ----------
        measurements : `list`, optional
            A list of `Measurement` JSON serializations.
        blob_set : `BlobSet`, optional
            A `BlobSet` instance that support measurement deserialization.
        metric_set : `MetricSet`, optional
            A `MetricSet` that supports measurement deserialization. If
            provided, measurements are validated for unit consistency
            with metric definitions. `Measurement` instances also gain a
            `Measurement.metric` attribute.

        Returns
        -------
        instance : `MeasurementSet`
            A `MeasurementSet` instance.
        """
        instance = cls()

        if measurements is None:
            measurements = []

        if len(metric_set) == 0:
            # Job.deserialize may pass an empty MetricSet, so ignore that
            metric_set = None

        for meas_doc in measurements:
            if metric_set is not None:
                try:
                    metric = metric_set[meas_doc['metric']]
                    meas_doc['metric'] = metric
                except KeyError:
                    # metric not in the MetricSet, but it's optional
                    pass
            meas = Measurement.deserialize(blobs=blob_set, **meas_doc)
            instance.insert(meas)
        return instance

    def __getitem__(self, key):
        if not isinstance(key, Name):
            key = Name(metric=key)

        return self._items[key]

    def __setitem__(self, key, value):
        if not isinstance(key, Name):
            key = Name(metric=key)

        if not key.is_metric:
            raise KeyError('Key {0} is not a metric name'.format(key))

        if not isinstance(value, Measurement):
            message = ('Measurement {0} is not a '
                       'lsst.verify.Measurement-type')
            raise TypeError(message.format(value))

        if key != value.metric_name:
            message = ("Key {0} is inconsistent with the measurement's "
                       "metric name, {1}")
            raise KeyError(message.format(key, value.metric_name))

        self._items[key] = value

    def __len__(self):
        return len(self._items)

    def __contains__(self, key):
        if not isinstance(key, Name):
            key = Name(metric=key)

        return key in self._items

    def __delitem__(self, key):
        if not isinstance(key, Name):
            key = Name(metric=key)

        del self._items[key]

    def __iter__(self):
        for key in self._items:
            yield key

    def __eq__(self, other):
        return self._items == other._items

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iadd__(self, other):
        """Merge another `MeasurementSet` into this one.

        Parameters
        ----------
        other : `MeasurementSet`
            Another `MeasurementSet`. Measurements in ``other`` that do
            exist in this set are added to this one. Measurements in
            ``other`` replace measurements of the same metric in this one.

        Returns
        -------
        self : `MeasurementSet`
            This `MeasurementSet`.

        Notes
        -----
        Equivalent to `update`.
        """
        self.update(other)
        return self

    def __str__(self):
        count = len(self)
        if count == 0:
            count_str = 'empty'
        elif count == 1:
            count_str = '1 Measurement'
        else:
            count_str = '{count:d} Measurements'.format(count=count)
        return '<MeasurementSet: {0}>'.format(count_str)

    def keys(self):
        """Get a sequence of metric names contained in the measurement set.

        Returns
        -------
        keys : sequence of `Name`
            Sequence of names of metrics for measurements in the set.
        """
        return self._items.keys()

    def items(self):
        """Iterete over (`Name`, `Measurement`) pairs in the set.

        Yields
        ------
        item : `tuple`
            Tuple containing:

            - `Name` of the measurement's `Metric`.
            - `Measurement` instance.
        """
        for item in self._items.items():
            yield item

    def insert(self, measurement):
        """Insert a measurement into the set."""
        self[measurement.metric_name] = measurement

    def update(self, other):
        """Merge another `MeasurementSet` into this one.

        Parameters
        ----------
        other : `MeasurementSet`
            Another `MeasurementSet`. Measurements in ``other`` that do
            exist in this set are added to this one. Measurements in
            ``other`` replace measurements of the same metric in this one.
        """
        for _, measurement in other.items():
            self.insert(measurement)

    def refresh_metrics(self, metric_set):
        r"""Refresh `Measurement.metric` attributes in `Measurement`\ s
        contained by this set.

        Parameters
        ----------
        metric_set : `MetricSet`
            `Metric`\ s from this set are inserted into corresponding
            `Measurement`\ s contained in this `MeasurementSet`.

        Notes
        -----
        This method is especially useful for inserting `Metric` instances into
        `Measurement`\ s that weren't originally created with `Metric`
        instances. By including a `Metric` in a `Measurement`, the serialized
        units of a measurment are normalized to the metric's definition.

        See also
        --------
        lsst.verify.Job.reload_metrics_package
        """
        for metric_name, measurement in self.items():
            if metric_name in metric_set:
                measurement.metric = metric_set[metric_name]

    @property
    def json(self):
        """A `dict` that can be serialized as JSON."""
        json_doc = JsonSerializationMixin._jsonify_list(
            [meas for name, meas in self.items()]
        )
        return json_doc
