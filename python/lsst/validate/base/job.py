# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

from .jsonmixin import JsonSerializationMixin
from .blob import BlobBase
from .measurement import MeasurementBase


__all__ = ['Job']


class Job(JsonSerializationMixin):
    """A `Job` wraps all measurements and blob metadata associated with a
    validation run.

    Measurements and blobs can be added both during initialization, or anytime
    afterwards with the `register_measurement` and `register_blob` methods.

    The `get_measurement` method lets you search for a stored measurement
    based on the `Metric` name (and filter or specification name, if the
    measurement is dependent on those).

    Use the `Job.json` attribute to access a json-serializable `dict` of all
    measurements and blobs associated with the `Job`.

    A `Job` can only contain measurements against one dataset at a time.
    Typically, `Job`\ s are uploaded to SQUASH separately for each tested
    dataset.

    Parameters
    ----------
    measurements : `list`, optional
        List of `MeasurementBase`-derived objects. Additional measurements can
        be added with the `register_measurement` method.
    blobs : `list`, optional
        List of `BlobBase`-derived objects. Additional blobs can be added
        with the `register_blob` method.
    """
    def __init__(self, measurements=None, blobs=None):
        self._measurements = []
        self._measurement_ids = set()
        self._blobs = []
        self._blob_ids = set()

        if measurements:
            for m in measurements:
                self.register_measurement(m)

        if blobs:
            for b in measurements:
                self.register_blob(b)

    def register_measurement(self, m):
        """Add a measurement object to the `Job`.

        Registering a measurement also automatically registers all
        linked blobs.

        Parameters
        ----------
        m : `MeasurementBase`-type object
            A measurement object.
        """
        assert isinstance(m, MeasurementBase)
        if m.identifier not in self._measurement_ids:
            self._measurements.append(m)
            self._measurement_ids.add(m.identifier)
            for name, b in m.blobs.items():
                self.register_blob(b)

    def get_measurement(self, metric_name, spec_name=None, filter_name=None):
        """Get a measurement corresponding to the given criteria.

        Parameters
        ----------
        metric_name : `str`
            Name of the `Metric` for the requested measurement.
        spec_name : `str`, optional
            Name of the specification level if the measurement algorithm is
            dependent on the specification level of a metric.
        filter_name : `str`, optional
            Name of the optical filter if the measurement is specific to a
            filter.

        Returns
        -------
        measurement : `MeasurementBase`-type object
            The single measurement instance that fulfills the search criteria.

        Raises
        ------
        RuntimeError
            Raised when a measurement cannot be found, either because no such
            measurement exists or because the request is ambiguous
            (``spec_name`` or ``filter_name`` need to be set).
        """
        candidates = [m for m in self._measurements if m.label == metric_name]
        if len(candidates) == 1:
            candidate = candidates[0]
            if spec_name is not None and candidate.spec_name is not None:
                assert candidate.spec_name == spec_name
            if filter_name is not None and candidate.filter_name is not None:
                assert candidate.filter_name == filter_name
            return candidate

        # Filter by spec_name
        if spec_name is not None:
            candidates = [m for m in candidates if m.spec_name == spec_name]
        if len(candidates) == 1:
            candidate = candidates[0]
            if filter_name is not None and candidate.filter_name is not None:
                assert candidate.filter_name == filter_name
            return candidate

        # Filter by filter_name
        if filter_name is not None:
            candidates = [m for m in candidates
                          if m.filter_name == filter_name]
        if len(candidates) == 1:
            return candidates[0]

        raise RuntimeError('Measurement not found', metric_name, spec_name)

    def register_blob(self, b):
        """Add a blob object to the `Job`.

        Parameters
        ----------
        b : `BlobBase`-type object
            A blob object.
        """
        assert isinstance(b, BlobBase)
        if b.identifier not in self._blob_ids:
            self._blobs.append(b)
            self._blob_ids.add(b.identifier)

    @property
    def json(self):
        """`Job` data as a JSON-serialiable `dict`."""
        doc = JsonSerializationMixin.jsonify_dict({
            'measurements': self._measurements,
            'blobs': self._blobs})
        return doc

    @property
    def metric_names(self):
        """Names of `Metric`\ s measured in this `Job` (`list`)."""
        metric_names = []
        for m in self._measurements:
            if m.value is not None:
                if m.metric.name not in metric_names:
                    metric_names.append(m.metric.name)
        return metric_names

    @property
    def spec_levels(self):
        """`list` of names of specification levels that are available for
        `Metric`\ s measured in this `Job`.
        """
        spec_names = []
        for m in self._measurements:
            for spec in m.metric.specs:
                if spec.name not in spec_names:
                    spec_names.append(spec.name)
        return spec_names
