# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

from .jsonmixin import JsonSerializationMixin
from .blob import BlobBase
from .measurement import MeasurementBase


__all__ = ['Job']


class Job(JsonSerializationMixin):
    """A Job is a wrapper around all measurements and blob metadata associated
    with a validation run.

    Use the Job.json attribute to access a json-serializable dict of all
    measurements and blobs associated with the Job.

    Parameters
    ----------
    measurements : `list`, optional
        List of `MeasurementBase`-derived objects.
    blobs : list
        List of `BlobBase`-derived objects.
    """
    def __init__(self, measurements=None, blobs=None):
        self._measurements = []
        self._measurement_ids = set()
        self._blobs = []
        self._blob_ids = set()

        if measurements:
            for m in measurements:
                self.registerMeasurement(m)

        if blobs:
            for b in measurements:
                self.registerBlob(b)

    def registerMeasurement(self, m):
        """Add a measurement object to the Job.

        Registering a measurement will also automatically register all
        linked blobs.

        Parameters
        ----------
        m : :class:`lsst.validate.base.MeasurementBase`-type object
            A measurement object.
        """
        assert isinstance(m, MeasurementBase)
        if m.identifier not in self._measurement_ids:
            self._measurements.append(m)
            self._measurement_ids.add(m.identifier)
            for name, b in m.blobs.items():
                self.registerBlob(b)

    def getMeasurement(self, metricName, specName=None, bandpass=None):
        """Get a measurement in corresponding to the given criteria
        within the job.
        """
        candidates = [m for m in self._measurements if m.label == metricName]
        if len(candidates) == 1:
            candidate = candidates[0]
            if specName is not None and candidate.specName is not None:
                assert candidate.specName == specName
            if bandpass is not None and candidate.bandpass is not None:
                assert candidate.bandpass == bandpass
            return candidate

        # Filter by specName
        if specName is not None:
            candidates = [m for m in candidates if m.specName == specName]
        if len(candidates) == 1:
            candidate = candidates[0]
            if bandpass is not None and candidate.bandpass is not None:
                assert candidate.bandpass == bandpass
            return candidate

        # Filter by bandpass
        if bandpass is not None:
            candidates = [m for m in candidates if m.bandpass == bandpass]
        if len(candidates) == 1:
            return candidates[0]

        raise RuntimeError('Measurement not found', metricName, specName)

    def registerBlob(self, b):
        """Add a blob object to the Job.

        Parameters
        ----------
        b : :class:`lsst.validate.base.BlobBase`-type object
            A blob object.
        """
        assert isinstance(b, BlobBase)
        if b.identifier not in self._blob_ids:
            self._blobs.append(b)
            self._blob_ids.add(b.identifier)

    @property
    def json(self):
        doc = JsonSerializationMixin.jsonify_dict({
            'measurements': self._measurements,
            'blobs': self._blobs})
        return doc

    @property
    def availableMetrics(self):
        metricNames = []
        for m in self._measurements:
            if m.value is not None:
                if m.metric.name not in metricNames:
                    metricNames.append(m.metric.name)
        return metricNames

    @property
    def availableSpecLevels(self):
        """List of spec names that available for metrics measured in this Job.
        """
        specNames = []
        for m in self._measurements:
            for spec in m.metric.specs:
                if spec.name not in specNames:
                    specNames.append(spec.name)
        return specNames
