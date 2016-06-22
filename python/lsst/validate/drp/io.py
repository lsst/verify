# LSST Data Management System
# Copyright 2008-2016 AURA/LSST.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
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

from __future__ import print_function, division, absolute_import

import uuid
import abc
import json
import numpy as np
import astropy.units
import lsst.pipe.base as pipeBase

from .base import BlobBase, MeasurementBase


class DatumSerializer(object):
    """Serializer for an annotated data point.

    Use the `DatumSerializer.json` property to convert a datum to a JSON-ready
    data structure.

    Parameters
    ----------
    value : `str`, `int`, `float` or 1-D iterable.
        Value of the datum.
    units : `str`
        Astropy-compatible units string. See
        http://docs.astropy.org/en/stable/units/
    label : `str`, optional
        Label suitable for plot axes (without units).
    description : `str`, optional
        Extended description.
    """

    def __init__(self, value, units, label=None, description=None):
        self._doc = {}
        self.value = value
        self.units = units
        self.label = label
        self.description = description

    @property
    def json(self):
        """Datum as a `dict` compatible with overall Job JSON schema."""
        # Copy the dict so that the serializer is immutable
        v = self.value
        if isinstance(v, np.ndarray):
            v = v.tolist()
        d = {
            'value': v,
            'units': self.units,
            'label': self.label,
            'description': self.description
        }
        return d

    @property
    def value(self):
        """Value of the datum (`str`, `int`, `float` or 1-D iterable.)."""
        return self._doc['value']

    @value.setter
    def value(self, v):
        self._doc['value'] = v

    @property
    def units(self):
        """Astropy-compatible unit string."""
        return self._doc['units']

    @units.setter
    def units(self, value):
        # verify that Astropy can parse the unit string
        if value is not None and value != 'millimag':
            print(value)
            astropy.units.Unit(value, parse_strict='raise')
        self._doc['units'] = value

    @property
    def label(self):
        """Label for plotting (without units)."""
        return self._doc['label']

    @label.setter
    def label(self, value):
        assert isinstance(value, basestring) or None
        self._doc['label'] = value

    @property
    def description(self):
        """Extended description of Datum."""
        return self._doc['description']

    @description.setter
    def description(self, value):
        assert isinstance(value, basestring) or None
        self._doc['description'] = value


class ParametersSerializerBase(object):
    """Baseclass for a Parameters serializer.

    Individual measurements should implement their own serializers to enforce
    specific schemas.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        self._doc = {}

    @property
    def json(self):
        d = ParametersSerializerBase.jsonify_dict(self._doc)
        d['schema_id'] = self.schema_id
        return d

    @staticmethod
    def jsonify_dict(d):
        json_dict = {}
        for k, v in d.iteritems():
            if isinstance(v, DatumSerializer):
                json_dict[k] = v.json
            elif isinstance(v, dict):
                json_dict[k] = ParametersSerializerBase.jsonify_dict(v)
            else:
                json_dict[k] = v
        return json_dict

    @abc.abstractproperty
    def schema_id(self):
        pass


class BlobSerializerBase(object):
    """Baseclass for a Blob serializer.

    Blobs are designed to flexibly store processed artifacts from measurement
    codes from which the scalar metric is derived. Blobs allow rich
    visualization to give context to scalar measurements.

    Multiple measurements can share the same blob. Blobs contain an :attr:`id`
    attribute that allows multple measurement documents to refer to the same
    blob.

    Individual measurements should implement their own serializers to enforce
    specific schemas.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        self._id = uuid.uuid4().hex
        self._doc = {}

    @property
    def json(self):
        """Measurement as a `dict` compatible with overall Job JSON schema."""
        d = BlobSerializerBase.jsonify_dict(self._doc)
        d['schema_id'] = self.schema_id
        d['id'] = self.id
        return d

    @staticmethod
    def jsonify_dict(d):
        json_dict = {}
        for k, v in d.iteritems():
            if isinstance(v, DatumSerializer):
                json_dict[k] = v.json
            elif isinstance(v, dict):
                json_dict[k] = BlobSerializerBase.jsonify_dict(v)
            else:
                json_dict[k] = v
        return json_dict

    @abc.abstractproperty
    def schema_id(self):
        pass

    @property
    def id(self):
        """Unique blob identifier."""
        return self._id


class MetricSerializer(object):
    """Serializer for a metric.

    Note that information about success thresholds is maintained separately
    from the metric definition.

    Parameters
    ----------
    name : `str`
        Metric name/identifier.
    spec_level : `str`, optional
        Level of a Metric Specification that this Metric corresponds to,
        if applicable. For example, PF1 is dependent on the specification
        level to determine PA2.
    reference : `str`, optional
        Document handle that defines this metric
    description : `str`, optional
        Long description of this metric.
    """

    def __init__(self, name, spec_level=None, reference=None, description=None):
        self._doc = {}
        self.name = name
        self.spec_level = spec_level
        self.reference = reference
        self.description = description

    @property
    def json(self):
        return dict(self._doc)

    @property
    def name(self):
        """Metric name/identifier (`str`)."""
        return self._doc['name']

    @name.setter
    def name(self, n):
        assert isinstance(n, basestring)
        self._doc['name'] = n

    @property
    def spec_level(self):
        """Metric specification level (`str` or `None`)."""
        return self._doc['spec_level']

    @spec_level.setter
    def spec_level(self, n):
        assert isinstance(n, basestring) or n is None
        self._doc['spec_level'] = n

    @property
    def reference(self):
        """Document handle that defines this metric (`str`)."""
        return self._doc['reference']

    @reference.setter
    def reference(self, n):
        assert isinstance(n, basestring)
        self._doc['reference'] = n

    @property
    def description(self):
        """Long description of this metric (`str`)."""
        return self._doc['description']

    @description.setter
    def description(self, n):
        assert isinstance(n, basestring)
        self._doc['description'] = n


class MeasurementSerializer(object):
    """Serializer for a measurement of a metric.

    Parameters
    ----------
    metric : `MetricSerializer`
        Serializer for metric definition.
    value : `DatumSerializer`
        Serializer for measured scalar metric value.
    parameters : `ParametersSerializerBase`
        Serializer with parameters for this measurement.
    blob_id : `BlobSerializerBase`, optional
        Identifier to reference a Blob with detailed metadata about this
        scalar metric measurement.
    """

    def __init__(self, metric, value, parameters, blob_id=None):
        self._doc = {}
        self.metric = metric
        self.value = value
        self.parameters = parameters
        self.blob_id = blob_id

    @property
    def json(self):
        """Measurement as a `dict` compatible with overall Job JSON schema."""
        d = {
            'metric': self.metric.json,
            'value': self.value.json,
            'parameters': self.parameters.json,
            'blob_id': self.blob_id
        }
        return d

    @property
    def metric(self):
        """A `MetricSerializer` instance."""
        return self._doc['metric']

    @metric.setter
    def metric(self, metric_doc):
        assert isinstance(metric_doc, MetricSerializer)
        self._doc['metric'] = metric_doc

    @property
    def value(self):
        return self._doc['value']

    @value.setter
    def value(self, measured_value):
        assert isinstance(measured_value, DatumSerializer)
        self._doc['value'] = measured_value

    @property
    def parameters(self):
        return self._doc['parameters']

    @parameters.setter
    def parameters(self, params):
        assert isinstance(params, ParametersSerializerBase)
        self._doc['parameters'] = params

    @property
    def blob_id(self):
        return self._doc['blob_id']

    @blob_id.setter
    def blob_id(self, name):
        assert isinstance(name, basestring)
        self._doc['blob_id'] = name


class JobSerializer(object):
    """Serializer for validate_drp processing jobs.

    Parameters
    ----------
    measurements : `list`
        List of `MeasurementSerializerBase`-type instances.
    blobs : `list`
        List of `BlobSerializerBase`-type instances.
    """

    def __init__(self, measurements, blobs=None):
        self._doc = {
            'measurements': [],
            'blobs': []
        }

        self.measurements = measurements
        self.blobs = blobs

    @property
    def json(self):
        """Measurement as a `dict` compatible with overall Job JSON schema."""
        d = {
            'measurements': [m.json for m in self.measurements],
            'blobs': [b.json for b in self.blobs]
        }
        return d

    @property
    def measurements(self):
        """`list` of Measurement serializers."""
        return self._doc['measurements']

    @measurements.setter
    def measurements(self, meas_serializers):
        for m in meas_serializers:
            assert isinstance(m, MeasurementBase)
            self._doc['measurements'].append(m)

    @property
    def blobs(self):
        """`list` of Blob serializers."""
        return self._doc['blobs']

    @blobs.setter
    def blobs(self, blob_serializers):
        for m in blob_serializers:
            assert isinstance(m, BlobBase)
            self._doc['blobs'].append(m)


class MultiVisitStarBlobSerializer(BlobSerializerBase):
    """Blob for datasets that match stars across multiple visits (with
    a single filter).

    This serializer is used with AMx, AFx, ADx, PA1, PA2 and PF1 metrics.
    """
    def __init__(self, **args):
        BlobSerializerBase.__init__(self)
        self._doc.update(args)

    @classmethod
    def init_from_structs(cls, bandpass, analyze_struct, astrom_struct, phot_struct):
        """Create a `MultiVisitStarBlobSerializer` from validate_drp's
        internal data structures.

        Parameters
        ----------
        bandpass : `str`
            Filter name (bandpass).
        analyze_struct : `lsst.pipebase.Struct`
            Stellar dataset statistics generated by
            `lsst.validate.drp.validate.analyzeData`.
        astrom_struct : `lsst.pipebase.Struct`
            Dataset produced by `lsst.validate.drp.check.checkAstrometry`.
        phot_struct : `lsst.pipebase.Struct`
            Dataset produced by `lsst.validate.drp.check.checkPhotometry`.
        """
        args = {}

        # Serialize analyze_struct
        args['mag'] = DatumSerializer(
            analyze_struct.mag,
            'mag',
            label='{band}'.format(band=bandpass),
            description='Mean PSF magnitudes of stars over multiple visits')
        args['mag_rms'] = DatumSerializer(
            analyze_struct.magrms,
            'mag',
            label='RMS({band})'.format(band=bandpass),
            description='RMS of PSF magnitudes over multiple visits')
        args['mag_err'] = DatumSerializer(
            analyze_struct.magerr,
            'mag',
            label='sigma({band})'.format(band=bandpass),
            description='Median 1-sigma uncertainty of PSF magnitudes over '
                        'multiple visits')
        args['snr'] = DatumSerializer(
            analyze_struct.snr,
            None,
            label='SNR({band})'.format(band=bandpass),
            description='Median signal-to-noise ratio of PSF magnitudes over '
                        'multiple visits')
        args['dist'] = DatumSerializer(
            analyze_struct.dist,
            'milliarcsecond',
            label='d',
            description='RMS of sky coordinates of stars over multiple visits')

        # serialize astrom_struct
        args[astrom_struct.model_name] = {}
        args[astrom_struct.model_name]['doc'] \
            = "Photometric uncertainty model: mas = C*theta/SNR + sigmaSys"
        args[astrom_struct.model_name]['C'] = DatumSerializer(
            astrom_struct.params['C'],
            None,
            label='C',
            description='Scaling factor')
        args[astrom_struct.model_name]['theta'] = DatumSerializer(
            astrom_struct.params['theta'],
            'milliarcsecond',  # TODO replace with 'thetaUnits'
            label='theta',
            description='Seeing')  # TODO
        args[astrom_struct.model_name]['sigmaSys'] = DatumSerializer(
            astrom_struct.params['sigmaSys'],
            'milliarcsecond',  # TODO replace with struct's units
            label='sigma(sys)',
            description='Systematic error floor')
        args['astrom_rms'] = DatumSerializer(
            astrom_struct.astromRmsScatter,
            'milliarcsecond',  # TODO replace with struct's units
            label='RMS',
            description='Astrometric scatter (RMS) for good stars')

        # serialize phot_struct
        args[phot_struct.model_name] = {}
        args[phot_struct.model_name]['doc'] \
            = "Photometric uncertainty model from " \
              "http://arxiv.org/abs/0805.2366v4 (Eq 4, 5): " \
              "sigma_1^2 = sigma_sys^2 + sigma_rand^2, " \
              "sigma_rand^2 = (0.04 - gamma) * x + gamma * x^2 [mag^2] " \
              "where x = 10**(0.4*(m-m_5))"
        args[phot_struct.model_name]['sigmaSys'] = DatumSerializer(
            phot_struct.params['sigmaSys'],
            'mag',
            label='sigma(sys)',
            description='Systematic error floor')
        args[phot_struct.model_name]['gamma'] = DatumSerializer(
            phot_struct.params['gamma'],
            None,
            label='gamma',
            description='Proxy for sky brightness and read noise')
        args[phot_struct.model_name]['m5'] = DatumSerializer(
            phot_struct.params['m5'],
            'mag',
            label='m5',
            description='5-sigma depth')  # TODO
        args['phot_rms'] = DatumSerializer(
            phot_struct.photRmsScatter,
            'millimag',
            label='RMS',
            description='RMS photometric scatter for good stars')

        return cls(**args)

    @property
    def schema_id(self):
        return 'multi-visit-star-blob-v1.0.0'


def persist_job(job, filepath):
    with open(filepath, 'w') as outfile:
        json_data = job.json
        json.dump(json_data, outfile, sort_keys=True, indent=2)


def saveKpmToJson(KpmStruct, filename):
    """Save KPM `lsst.pipe.base.Struct` to JSON file.

    Parameters
    ----------
    KpmStruct : lsst.pipe.base.Struct
        Information to serialize in JSON.
    filename : str
        Output filename.

    Examples
    --------
    >>> import lsst.pipe.base as pipeBase
    >>> foo = pipeBase.Struct(a=2)
    >>> outfile = 'tmp.json'
    >>> saveKpmToJson(foo, outfile)

    Notes
    -----
    Rewrites `numpy.ndarray` as a list`
    """
    data = KpmStruct.getDict()

    # Simple check to convert numpy.ndarray to list
    for k, v in data.iteritems():
        if isinstance(v, np.ndarray):
            data[k] = v.tolist()

    with open(filename, 'w') as outfile:
        # Structure the output with sort_keys, and indent
        # to make comparisons of output results easy on a line-by-line basis.
        json.dump(data, outfile, sort_keys=True, indent=4)


def loadKpmFromJson(filename):
    """Load KPM `lsst.pipe.base.Struct` from JSON file.

    Parameters
    ----------
    filename : str
        Input filename.

    Returns
    -------
    KpmStruct : lsst.pipe.base.Struct
        Reconstructed information from file reconstructed

    Examples
    --------
    >>> import lsst.pipe.base as pipeBase
    >>> foo = pipeBase.Struct(a=2)
    >>> outfile = 'tmp.json'
    >>> saveKpmToJson(foo, outfile)
    >>> bar = loadKpmFromJson(outfile)
    >>> print(bar.a)
    2

    Notes
    -----
    Rewrites `numpy.ndarray` as a list`
    """

    with open(filename, 'r') as infile:
        data = json.load(infile)

    return pipeBase.Struct(**data)
