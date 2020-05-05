# This file is part of verify.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
__all__ = ['Job']

import json
import os

from .blobset import BlobSet
from .jobmetadata import Metadata
from .jsonmixin import JsonSerializationMixin
from .measurementset import MeasurementSet
from .metricset import MetricSet
from .specset import SpecificationSet
from . import squash


class Job(JsonSerializationMixin):
    r"""Container for `~lsst.verify.Measurement`\ s, `~lsst.verify.Blob` \s,
    and `~lsst.verify.Metadata` associated with a pipeline run.

    Parameters
    ----------
    measurements : `MeasurementSet` or `list` of `Measurement`\ s, optional
        `Measurement`\ s to report in the Job.
    metrics : `list` of `Metric`\ s or a `MetricSet`, optional
        Optional list of `Metric`\ s, or a `MetricSet`.
    specs : `SpecificationSet` or `list` of `Specification`\ s, optional
        Optional specification information.
    meta : `dict`, optional
        Optional dictionary of metadata key-value entries.
    """

    def __init__(self, measurements=None, metrics=None, specs=None,
                 meta=None):
        if isinstance(measurements, MeasurementSet):
            self._meas_set = measurements
        else:
            self._meas_set = MeasurementSet(measurements)

        if isinstance(metrics, MetricSet):
            self._metric_set = metrics
        else:
            self._metric_set = MetricSet(metrics)

        if isinstance(specs, SpecificationSet):
            self._spec_set = specs
        else:
            self._spec_set = SpecificationSet(specs)

        # Create metadata last so it has access to the measurement set
        self._meta = Metadata(self._meas_set, data=meta)

    @classmethod
    def load_metrics_package(cls, package_name_or_path='verify_metrics',
                             subset=None, measurements=None, meta=None):
        r"""Create a Job with metrics and specifications pre-loaded from a
        Verification Framework metrics package, such as
        :ref:`verify_metrics <verify-metrics-package>`.

        Parameters
        ----------
        package_name_or_path : `str`, optional
            Name of an EUPS package that hosts metric and specification
            definition YAML files **or** the file path to a metrics package.
            ``'verify_metrics'`` is the default package, and is where metrics
            and specifications are defined for most LSST Science Pipelines
            packages.
        subset : `str`, optional
            If set, only metrics and specification for this package are loaded.
            For example, if ``subset='validate_drp'``, only ``validate_drp``
            metrics are loaded. This argument is equivalent to the
            `MetricSet.subset` method. Default is `None`.
        measurements : `MeasurementSet` or `list` of `Measurement`\ s, optional
            Measurements to report in the Job.
        meta : `dict`, optional
            Optional dictionary of metadata key-value entries to include
            in the Job.

        Returns
        -------
        job : `Job`
            `Job` instance.
        """
        metrics = MetricSet.load_metrics_package(
            package_name_or_path=package_name_or_path,
            subset=subset)
        specs = SpecificationSet.load_metrics_package(
            package_name_or_path=package_name_or_path,
            subset=subset)
        instance = cls(measurements=measurements, metrics=metrics, specs=specs,
                       meta=meta)
        return instance

    @classmethod
    def deserialize(cls, measurements=None, blobs=None,
                    metrics=None, specs=None, meta=None):
        """Deserialize a Verification Framework Job from a JSON serialization.

        Parameters
        ----------
        measurements : `list`, optional
            List of serialized `Measurement` objects.
        blobs : `list`, optional
            List of serialized `Blob` objects.
        metrics : `list`, optional
            List of serialized `Metric` objects.
        specs : `list`, optional
            List of serialized specification objects.
        meta : `dict`, optional
            Dictionary of key-value metadata entries.

        Returns
        -------
        job : `Job`
            `Job` instance built from serialized data.

        Examples
        --------
        Together, `Job.json` and `Job.deserialize` allow a verification job to
        be serialized and later re-instantiated.

        >>> import json
        >>> job = Job()
        >>> json_str = json.dumps(job.json)
        >>> json_obj = json.loads(json_str)
        >>> new_job = Job.deserialize(**json_obj)
        """
        blob_set = BlobSet.deserialize(blobs)
        metric_set = MetricSet.deserialize(metrics)
        spec_set = SpecificationSet.deserialize(specs)
        meas_set = MeasurementSet.deserialize(
            measurements=measurements,
            blob_set=blob_set,
            metric_set=metric_set)

        instance = cls(measurements=meas_set,
                       metrics=metric_set,
                       specs=spec_set,
                       meta=meta)
        return instance

    @property
    def measurements(self):
        """Measurements associated with the pipeline verification job
        (`MeasurementSet`).
        """
        return self._meas_set

    @property
    def metrics(self):
        """Metrics associated with the pipeline verification job (`MetricSet`).
        """
        return self._metric_set

    @property
    def specs(self):
        """Specifications associated with the pipeline verifification job
        (`SpecificationSet`).
        """
        return self._spec_set

    @property
    def meta(self):
        """Metadata mapping (`Metadata`)."""
        return self._meta

    @property
    def json(self):
        """`Job` data as a JSON-serialiable `dict`."""
        # Gather blobs from all measurements
        blob_set = BlobSet()
        for name, measurement in self._meas_set.items():
            for blob_name, blob in measurement.blobs.items():
                if (str(name) == blob_name) and (len(blob) == 0):
                    # Don't serialize empty 'extras' blobs
                    continue
                blob_set.insert(blob)

        doc = JsonSerializationMixin.jsonify_dict({
            'measurements': self._meas_set,
            'blobs': blob_set,
            'metrics': self._metric_set,
            'specs': self._spec_set,
            'meta': self._meta
        })
        return doc

    def __eq__(self, other):
        if self.measurements != other.measurements:
            return False

        if self.metrics != other.metrics:
            return False

        if self.specs != other.specs:
            return False

        if self.meta != other.meta:
            return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iadd__(self, other):
        """Merge another Job into this one.

        Parameters
        ----------
        other : `Job`
            Job instance to be merged into this one.

        Returns
        -------
        self : `Job`
            This `Job` instance.
        """
        self.measurements.update(other.measurements)
        self.metrics.update(other.metrics)
        self.specs.update(other.specs)
        self.meta.update(other.meta)
        return self

    def reload_metrics_package(self, package_name_or_path='verify_metrics',
                               subset=None):
        """Load a metrics package and add metric and specification definitions
        to the Job, as well as the collected measurements.

        Parameters
        ----------
        package_name_or_path : `str`, optional
            Name of an EUPS package that hosts metric and specification
            definition YAML files **or** the file path to a metrics package.
            ``'verify_metrics'`` is the default package, and is where metrics
            and specifications are defined for most packages.
        subset : `str`, optional
            If set, only metrics and specification for this package are loaded.
            For example, if ``subset='validate_drp'``, only ``validate_drp``
            metrics are included in the `MetricSet`. This argument is
            equivalent to the `MetricSet.subset` method. Default is `None`.

        Notes
        -----
        This method is useful for loading metric and specification definitions
        into a job that was created without this information. In addition
        to being added to `Job.metrics`, metrics are also attached to
        `Job.measurements` items. This ensures that measurement values are
        normalized into the units of the metric definition when a Job is
        serialized.

        See also
        --------
        lsst.verify.MeasurementSet.refresh_metrics
        """
        metrics = MetricSet.load_metrics_package(
            package_name_or_path=package_name_or_path,
            subset=subset)
        specs = SpecificationSet.load_metrics_package(
            package_name_or_path=package_name_or_path,
            subset=subset)

        self.metrics.update(metrics)
        self.specs.update(specs)

        # Insert mertics into measurements
        self.measurements.refresh_metrics(metrics)

    def write(self, filename):
        """Write a JSON serialization to the filesystem.

        Parameters
        ----------
        filename : `str`
            Name of the JSON file (including directories). This name
            should be unique among all task executions in a pipeline. The
            recommended extension is ``'.verify.json'``. This convention is
            used by post-processing tools to discover verification framework
            outputs.
        """
        dirname = os.path.dirname(filename)
        if len(dirname) > 0:
            if not os.path.isdir(dirname):
                os.makedirs(dirname)

        with open(filename, 'w') as f:
            json.dump(self.json, f, indent=2, sort_keys=True)

    def dispatch(self, api_user=None, api_password=None,
                 api_url='https://squash-restful-api.lsst.codes',
                 **kwargs):
        """POST the job to SQUASH, LSST Data Management's metric dashboard.

        Parameters
        ----------
        api_url : `str`, optional
            Root URL of the SQUASH API server.
        api_user : `str`, optional
            API username.
        api_password : `str`, optional
            API password.
        **kwargs : optional
            Additional keyword arguments passed to `lsst.verify.squash.post`.
        """
        full_json_doc = self.json
        # subset JSON to just the 'job' fields; no metrics and specs
        job_json = {k: full_json_doc[k]
                    for k in ('measurements', 'blobs', 'meta')}

        access_token = squash.get_access_token(api_url, api_user,
                                               api_password)

        squash.post(api_url, 'job', json_doc=job_json,
                    access_token=access_token, **kwargs)

    def report(self, name=None, spec_tags=None, metric_tags=None):
        r"""Create a verification report that lists the pass/fail status of
        measurements against specifications in this job.

        In a Jupyter notebook, this report can be shown as an inline table.

        Parameters
        ----------
        name : `str` or `lsst.verify.Name`, optional
            A package or metric name to subset specifications by. When set,
            only measurement and specification combinations belonging to that
            package or metric are included in the report.
        spec_tags : sequence of `str`, optional
            A set of specification tag strings. when given, only
            specifications that have all the given tags are included in the
            report. For example, ``spec_tags=['LPM-17', 'minimum']``.
        metric_tags : sequence of `str`, optional
            A set of metric tag strings. When given, only specifications
            belonging to metrics that posess **all** given tags are included
            in the report. For example,
            ``metric_tags=['LPM-17', 'photometry']`` selects sepifications
            that have both the ``'LPM-17'`` and ``'photometry'`` tags.

        Returns
        -------
        report : `lsst.verify.Report`
            Report instance. In a Jupyter notebook, you can view the report
            by calling `Report.show`.

        See also
        --------
        lsst.verify.SpecificationSet.report

        Notes
        -----
        This method uses the `lsst.verify.SpecificationSet.report` API to
        create the `lsst.verify.Report`, automatically inserting the `Job`\ 's
        measurements and metadata for filtering specifiation tests.

        In a Jupyter notebook environment, use the `lsst.verify.Report.show`
        method to view an interactive HTML table.

        .. code-block:: python

           job = lsst.verify.Job()
           # ...
           report = job.report()
           report.show()
        """
        report = self.specs.report(self.measurements, meta=self.meta,
                                   name=name, metric_tags=metric_tags,
                                   spec_tags=spec_tags, metrics=self.metrics)
        return report
