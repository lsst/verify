# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

__all__ = ['Job']

from .blobset import BlobSet
from .jsonmixin import JsonSerializationMixin
from .measurementset import MeasurementSet
from .metric import MetricSet
from .specset import SpecificationSet


class Job(JsonSerializationMixin):
    """Container for measurements, blobs, and provenance associated with a
    pipeline run.

    Parameters
    ----------
    measurements : `MeasurementSet` or `list` of `Measurement`\ s, optional
        Measurements to report in the Job.
    metrics : `list` of `Metric`\ s or a `MetricSet`, optional
        Optional list of metrics, or a `MetricSet`.
    specs : `SpecificationSet` or `list` of `Specification`\ s, optional
        Optional specification information.
    """

    def __init__(self, measurements=None, metrics=None, specs=None):
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

    @classmethod
    def load_metrics_package(cls, package_name_or_path='verify_metrics',
                             subset=None, measurements=None):
        """Create a Job with metrics and specifications pre-loaded from a
        Verification Framework metrics package.

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
        measurements : `MeasurementSet` or `list` of `Measurement`\ s, optional
            Measurements to report in the Job.

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
        instance = cls(measurements=measurements, metrics=metrics, specs=specs)
        return instance

    @classmethod
    def deserialize(cls, measurements=None, blobs=None,
                    metrics=None, specs=None):
        """Deserialize a Verification Framework Job from a JSON serialization.

        Parameters
        ----------
        measurements : `list`, optional
            List of serialized measurement objects.
        blobs : `list`, optional
            List of serialized blob objects.
        metrics : `list`, optional
            List of serialized metric objects.
        specs : `list`, optional
            List of serialized specification objects.

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
                       specs=spec_set)
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
            'specs': self._spec_set
        })
        return doc

    def __eq__(self, other):
        if self.measurements != other.measurements:
            return False

        if self.metrics != other.metrics:
            return False

        if self.specs != other.specs:
            return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)
