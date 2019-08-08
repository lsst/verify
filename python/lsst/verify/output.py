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

__all__ = ['output_quantities']

from .job import Job
from .measurement import Measurement
from .naming import Name


def output_quantities(package_name, quantities, suffix=None,
                      include_metrics=False, metrics_package='verify_metrics'):
    r"""Output measurements, as `astropy.units.Quantity` objects, from a
    pipeline task execution to a `lsst.verify`-formatted JSON file.

    Parameters
    ----------
    package_name : `str`
        Name of the package producing measurements. This name is used two ways:

        1. Make fully-qualified metric names from keys in the ``quantities``
           dictionary. For example, if a ``quantities`` dict has a key-value
           pair ``{'PA1': 5 * u.mmag}`` and ``package_name='validate_drp'``,
           the fully-qualified metric name is ``'validate_drp.PA1'``.
        2. As a filename prefix for the output JSON file.

    quantities : `dict` of `astropy.units.Quantity` values
        Dictionary of measurements as plain `astropy.units.Quantity`
        instances. Each key is the name of a metric. If metric names are
        not fully-specified (in ``package.metric`` format), the package
        name can be provided with the ``package_name`` argument.

    suffix : `str`, optional
        Additional suffix to add to the output JSON filename::

            {package_name}_{suffix}.verify.json

        The suffix may be used to distinguish measurement output files from
        different tasks in the same package.

    include_metrics : `bool`, optional
        Metric and specification definitions are included in the JSON output
        if set to `True`. The metric and specification definitions are
        loaded from a metric package indicated by the ``metrics_package``
        argument. Normally tasks do not need to include metric definitions if
        a post-processing step is used. Default: `False`.

    metrics_package : `str`, optional
        Name of the metrics package to obtain metrics from if
        ``include_metrics`` is `True`. Default is ``'verify_metrics'``.

    Returns
    -------
    filename : `str`
        Filename where the JSON file was written.

    See also
    --------
    lsst.verify.Job.write

    Notes
    -----
    This function is designed for lightweight `lsst.verify` framework usage.
    Rather than maintaining `Job` and `Measurement` objects,
    a task can simply record metric measurements as `astropy.units.Quantity`
    objects. With `output_quantities`, the task can output these measurements
    in a standardized `lsst.verify` JSON format. Post-processing tools
    can load this data for local analysis, or submit it to the
    https://squash.lsst.codes dashboard service.

    Tasks that need to include `Blob`\ s, `Measurement.extras` or query
    `Metric` objects should create a `Job` instance and use
    `Job.write` instead.
    """
    if include_metrics:
        job = Job.load_metrics_package(metrics_package, subset=package_name)
    else:
        job = Job()

    for name, quantity in quantities.items():
        metric_name = Name(package=package_name, metric=name)
        measurement = Measurement(metric_name, quantity=quantity)
        job.measurements.insert(measurement)

    if suffix is not None:
        filename = '{package}_{suffix}.verify.json'.format(
            package=package_name, suffix=suffix)
    else:
        filename = '{package}.verify.json'.format(package=package_name)

    job.write(filename)

    return filename
