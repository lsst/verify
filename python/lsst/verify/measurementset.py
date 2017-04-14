# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

__all__ = ['MeasurementSet']

from .measurement import Measurement


class MeasurementSet(object):
    """A collection of Measurements of Metrics, associated with a MetricSet.

    Parameters
    ----------
    name : `str`
        The name of this `MetricSet` (usually the name of a package).
    measurements : `dict` of `str`: `astropy.Quantity`
        The measurements (astropy.Quantities) of each metric, keyed on the
        metric name, to be looked up in metric_set.
    job : `Job`, optional
        The Job that produced these `Measurements`, linking them to their
        provenance and other metadata.
    metric_set : MetricSet, optional
        A `MetricSet` to extract the metric definitions from. If None, use
        name from the verify_metrics package.
    """
    name = None
    """`str` the name of the `MetricSet` these `Measurement`s are of."""

    measurements = None
    """`dict` of all `Measurement` names to `Measurement`s."""

    job = None
    """`Job` that this MeasurementSet was produced by."""

    def __init__(self, name, measurements, job=None, metric_set=None):
        if metric_set is None:
            raise NotImplementedError('Cannot autoload verify_metrics yet')
        self.name = name
        self.measurements = {}
        self.job = job
        for m, v in measurements.items():
            self.measurements[m] = Measurement(m, v, metric_set=metric_set)

    def __getitem__(self, key):
        return self.measurements[key]

    def __len__(self):
        return len(self.measurements)

    def __str__(self):
        items = ",\n".join(str(self.measurements[k])
                           for k in sorted(self.measurements))
        return "{0.name}: {{\n{1}\n}}".format(self, items)
