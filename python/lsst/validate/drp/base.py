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

from __future__ import print_function, division

import abc
import os
import json
import uuid
import operator
import yaml
import numpy as np
import astropy.units

from lsst.utils import getPackageDir


class ValidateError(Exception):
    """Base classes for exceptions in validate_drp."""
    pass


class ValidateErrorNoStars(ValidateError):
    """To be raised by tests that find no stars satisfying a set of criteria.

    Some example cases that might return such an error:
    1. There are no stars between 19-21 arcmin apart.
    2. There are no stars in the given magnitude range.
    """
    pass


class ValidateErrorSpecification(ValidateError):
    """Indicates an error with accessing or using requirement specifications."""
    pass


class ValidateErrorUnknownSpecificationLevel(ValidateErrorSpecification):
    """Indicates the requested level of requirements is unknown."""
    pass


class JsonSerializationMixin(object):
    """Mixin that provides serialization support"""

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def json(self):
        """a `dict` that can be serialized as semantic SQuaSH json."""
        pass

    @staticmethod
    def jsonify_dict(d):
        """Recursively render JSON on all values in a dict."""
        json_dict = {}
        for k, v in d.iteritems():
            json_dict[k] = JsonSerializationMixin._jsonify_value(v)
        return json_dict

    @staticmethod
    def jsonify_list(lst):
        json_array = []
        for v in lst:
            json_array.append(JsonSerializationMixin._jsonify_value(v))
        return json_array

    @staticmethod
    def _jsonify_value(v):
        if isinstance(v, JsonSerializationMixin):
            return v.json
        elif isinstance(v, dict):
            return JsonSerializationMixin.jsonify_dict(v)
        elif isinstance(v, (list, tuple)):
            return JsonSerializationMixin.jsonify_list(v)
        else:
            return v

    def write_json(self, filepath):
        """Write JSON to `filepath` on disk."""
        with open(filepath, 'w') as outfile:
            json.dump(self.json, outfile, sort_keys=True, indent=2)


class Datum(JsonSerializationMixin):
    """A value annotated with units, a plot label and description.

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
        if value is not None:
            astropy.units.Unit(value, parse_strict='raise')
        self._doc['units'] = value

    @property
    def latex_units(self):
        """Units as a LateX string, wrapped in ``$``."""
        if self.units != '':
            fmtr = astropy.units.format.Latex()
            return fmtr.to_string(self.astropy_units)
        else:
            return ''

    @property
    def astropy_units(self):
        """Astropy unit object."""
        return astropy.units.Unit(self.units)

    @property
    def astropy_quanitity(self):
        """Datum as an astropy Quantity."""
        return self.value * self.astropy_units

    @property
    def label(self):
        """Label for plotting (without units)."""
        return self._doc['label']

    @label.setter
    def label(self, value):
        assert isinstance(value, basestring) or value is None
        self._doc['label'] = value

    @property
    def description(self):
        """Extended description of Datum."""
        return self._doc['description']

    @description.setter
    def description(self, value):
        assert isinstance(value, basestring) or value is None
        self._doc['description'] = value


class Metric(JsonSerializationMixin):
    """Container for the definition of a Metric and specification levels.

    Parameters
    ----------
    name : str
        Name of the metric (e.g., PA1).
    description : str
        Short description about the metric.
    operatorStr : str
        A string, such as `'<='`, that defines a success test for a
        measurement (on the left hand side) against the metric specification
        level (right hand side).
    specs : list, optional
        A list of `Specification` objects that define various specification
        levels for this metric.
    referenceDoc : str, optional
        The document handle that originally defined the metric (e.g. LPM-17)
    referenceUrl : str, optional
        The document's URL.
    referencePath : str, optional
        Page where metric in defined in the reference document.
    """
    def __init__(self, name, description, operatorStr, specs=None,
                 referenceDoc=None, referenceUrl=None, referencePage=None):
        self.name = name
        self.description = description
        self.referenceDoc = referenceDoc
        self.referenceUrl = referenceUrl
        self.referencePage = referencePage

        self._operatorStr = operatorStr
        self.operator = Metric.convertOperatorString(operatorStr)

        if specs is None:
            self.specs = []
        else:
            self.specs = specs

    @classmethod
    def fromYaml(cls, metricName, yamlDoc=None, yamlPath=None,
                 resolveDependencies=True):
        """Create a `Metric` instance from YAML document that defines
        metrics.

        Parameters
        ----------
        metricName : str
            Name of the metric (e.g., PA1)
        yamlDoc : dict, optional
            The full metrics.yaml file loaded as a `dict`. Use this option
            to increase performance by eliminating redundant reads of a
            metrics.yaml file.
        yamlPath : str, optional
            The full path to a metrics.yaml file, in case a custom file
            is being used. The metrics.yaml file included in `validate_drp`
            is used by default.
        resolveDependencies : bool, optional
            If another metric is a *dependency* of this specification level's
            definition
        """
        if yamlDoc is None:
            if yamlPath is None:
                yamlPath = os.path.join(getPackageDir('validate_drp'),
                                        'metrics.yaml')
            with open(yamlPath) as f:
                yamlDoc = yaml.load(f)
        metricDoc = yamlDoc[metricName]

        m = cls(
            metricName,
            description=metricDoc.get('description', None),
            operatorStr=metricDoc['operator'],
            referenceDoc=metricDoc['reference'].get('doc', None),
            referenceUrl=metricDoc['reference'].get('url', None),
            referencePage=metricDoc['reference'].get('page', None))

        for specDoc in metricDoc['specs']:
            deps = None
            if 'dependencies' in specDoc and resolveDependencies:
                deps = {}
                for depItem in specDoc['dependencies']:
                    if isinstance(depItem, basestring):
                        # This is a metric
                        name = depItem
                        d = Metric.fromYaml(name, yamlDoc=yamlDoc,
                                            resolveDependencies=False)
                    elif isinstance(depItem, dict):
                        # Likely a Datum
                        # in yaml, wrapper object is dict with single key-val
                        name = depItem.keys()[0]
                        depItem = dict(depItem[name])
                        v = depItem['value']
                        units = depItem['units']
                        d = Datum(v, units,
                                  label=depItem.get('label', None),
                                  description=depItem.get('description', None))
                    else:
                        raise RuntimeError(
                            'Cannot process dependency %r' % depItem)
                    deps[name] = d
            spec = Specification(name=specDoc['level'],
                                 value=specDoc['value'],
                                 units=specDoc['units'],
                                 bandpasses=specDoc.get('filters', None),
                                 dependencies=deps)
            m.specs.append(spec)

        return m

    @property
    def reference(self):
        """A nicely formatted reference string."""
        refStr = ''
        if self.referenceDoc and self.referencePage:
            refStr = '{doc}, p. {page:d}'.format(doc=self.referenceDoc,
                                                 page=self.referencePage)
        elif self.referenceDoc:
            refStr = self.referenceDoc

        if self.referenceUrl and self.referenceDoc:
            refStr += ', {url}'.format(url=self.referenceUrl)
        elif self.referenceUrl:
            refStr = self.referenceUrl

        return refStr

    @staticmethod
    def convertOperatorString(opStr):
        """Convert a string representing a binary comparison operator to
        an operator function itself.

        Operators are designed so that the measurement is on the left-hand
        side, and specification level on the right hand side.

        The following operators are permitted:

        =====  ===========
        opStr  opFunc
        =====  ===========
        >=     operator.ge
        >      operator.gt,
        <      operator.lt,
        <=     operator.le
        ==     operator.eq
        !=     operator.ne
        =====  ===========

        Parameters
        ----------
        opStr : str
            A string representing a binary operator.

        Returns
        -------
        opFunc : obj
            An operator function from the :mod:`operator` standard library
            module.
        """
        operators = {'>=': operator.ge,
                     '>': operator.gt,
                     '<': operator.lt,
                     '<=': operator.le,
                     '==': operator.eq,
                     '!=': operator.ne}
        return operators[opStr]

    def getSpec(self, name, bandpass=None):
        """Get a specification by name, and other qualitifications.

        Parameters
        ----------
        name : str
            Name of a specification level (design, minimum, stretch).
        bandpass : str, optional
            The name of the bandpass to qualify a bandpass-dependent
            specification level.

        Returns
        -------
        spec : :class:`Specification`
            The :class:`Specification` that matches the name and other
            qualifications.

        Raises
        ------
        RuntimeError
           If a specification cannot be found.
        """
        # First collect candidate specifications by name
        candidates = [s for s in self.specs if s.name == name]

        if len(candidates) == 1:
            return candidates[0]

        # Filter down by bandpass
        if bandpass is not None:
            candidates = [s for s in candidates if bandpass in s.bandpasses]
        if len(candidates) == 1:
            return candidates[0]

        raise RuntimeError(
            'No {2} spec found for name={0} bandpass={1}'.format(
                name, bandpass, self.name))

    def getSpecNames(self, bandpass=None):
        """List names of all specification levels defined for this metric;
        optionally filtering by attributes such as bandpass.

        Parameters
        ----------
        bandpass : str, optional
            Name of the applicable filter, if needed.

        Returns
        -------
        specNames : list
            Specific names as a list of strings,
            e.g. ``['design', 'minimum', 'stretch']``.
        """
        specNames = []

        for spec in self.specs:
            if (bandpass is not None) and (spec.bandpasses is not None) \
                    and (bandpass not in spec.bandpasses):
                continue
            specNames.append(spec.name)

        return list(set(specNames))

    def checkSpec(self, value, specName, bandpass=None):
        """Compare a measurement `value` against a named specification level
        (:class:`SpecLevel`).

        Returns
        -------
        passed : bool
            `True` if a value meets the specification, `False` otherwise.
        """
        spec = self.getSpec(specName, bandpass=bandpass)

        # NOTE: assumes units are the same
        return self.operator(value, spec.value)

    @property
    def json(self):
        """Render metric as a JSON object (`dict`)."""
        return JsonSerializationMixin.jsonify_dict({
            'name': self.name,
            'reference': self.referenceDoc,
            'description': self.description,
            'specifications': self.specs})


class Specification(JsonSerializationMixin):
    """A specification level or threshold associated with a Metric."""
    def __init__(self, name, value, units, bandpasses=None, dependencies=None):
        self.name = name
        self.value = value
        self.units = units
        self.bandpasses = bandpasses
        self.dependencies = dependencies

    def __getattr__(self, key):
        """Access dependencies with keys as attributes."""
        return self.dependencies[key]

    @property
    def datum(self):
        """Representation of this Specification as a
        :class:`lsst.validate.drp.base.Datum`.
        """
        return Datum(self.value, units=self.units, label=self.name,
                     description=None)

    @property
    def latex_units(self):
        """Units as a LateX string, wrapped in ``$``."""
        if self.units != '':
            fmtr = astropy.units.format.Latex()
            return fmtr.to_string(self.astropy_units)
        else:
            return ''

    @property
    def astropy_units(self):
        """Astropy unit object."""
        return astropy.units.Unit(self.units)

    @property
    def astropy_quanitity(self):
        """Datum as an astropy Quantity."""
        return self.value * self.astropy_units

    @property
    def json(self):
        return JsonSerializationMixin.jsonify_dict({
            'name': self.name,
            'value': Datum(self.value, self.units),
            'filters': self.bandpasses,
            'dependencies': self.dependencies})


class MeasurementBase(JsonSerializationMixin):
    """Baseclass for Measurement classes.

    Attributes
    ----------
    metric
    units
    label
    json
    schema
    specName : str
        A `str` identifying the specification level (e.g., design, minimum
        stretch) that this measurement represents. `None` if this measurement
        applies to all specification levels.
    bandpass : str
        A `str` identifying the bandpass of observatons this measurement was
        made from. Defaults to `None` if a measurement is not
        bandpass-dependent. `bandpass` should be specificed if needed to
        resolve a bandpass-specific specification.
    parameters : dict
        A `dict` containing all input parameters used by this measurement.
        Parameters are :class:`lsst.validate.drp.base.Datum` instances.
        Parameters can be *accessed* directly from this attribute, but should
        be *set* with the :meth:`MeasurementBase.registerParameter` method.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._linkedBlobs = []
        self._id = uuid.uuid4().hex
        self.parameters = {}
        self.specName = None
        self.bandpass = None

    def linkBlob(self, blob):
        """Add a blob so that it will be linked to this measurement in
        the serialized JSON. This does not cause the blob itself to be
        persisted in a Job document, however.
        """
        self._linkedBlobs.append(blob)

    @property
    def blobs(self):
        return self._linkedBlobs

    @property
    def identifier(self):
        return self._id

    def registerParameter(self, paramKey, paramValue, units=None, label=None,
                          description=None):
        """Register a measurement input parameter so that it can be persisted
        with the measurement.

        Parameters are stored as :class:`Datum` objects, and can be
        accessed through the `parameters` attribute `dict`.

        Parameters
        ----------
        paramKey : str
            Name of the parameter; used as the key in the `parameters`
            attribute of this object.
        paramValue : obj or :class:`lsst.validate.drp.base.Datum`
            Value of the parameter, either as a regular object, or already
            represented as a :class:`~lsst.validate.drp.base.Datum`.
        units : str, optional
            The astropy-compatible unit string, used if `paramValue` is
            not already a `Datum`. See
            http://docs.astropy.org/en/stable/units/.
        label : str, optional
            Label suitable for plot axes (without units); used if
            `paramValue` is not already a `Datum`.
        description : `str`, optional
            Extended description; used if `paramValue` is not already a
            `Datum`.
        """
        if isinstance(paramValue, Datum):
            self.parameters[paramKey] = paramValue
        else:
            self.parameters[paramKey] = Datum(
                paramValue, units=units, label=label, description=description)

    @abc.abstractproperty
    def metric(self):
        """An instance derived from
        :class:`~lsst.validate.drp.base.MetricBase`.
        """
        pass

    @abc.abstractproperty
    def value(self):
        """Metric measurement value."""
        pass

    @abc.abstractproperty
    def units(self):
        """Astropy-compatible units string. (`str`)."""
        pass

    @property
    def latex_units(self):
        """Units as a LateX string, wrapped in ``$``."""
        if self.units != '':
            fmtr = astropy.units.format.Latex()
            return fmtr.to_string(self.astropy_units)
        else:
            return ''

    @property
    def astropy_units(self):
        """Astropy unit object."""
        return astropy.units.Unit(self.units)

    @abc.abstractproperty
    def label(self):
        """Lable (`str`) suitable for plot axes; without units."""
        pass

    @property
    def datum(self):
        """Representation of this measurement as a
        :class:`lsst.validate.drp.base.Datum`.
        """
        return Datum(self.value, units=self.units, label=self.label,
                     description=self.metric.description)

    @abc.abstractproperty
    def schema(self):
        """A `str` identifying the schema of this measurement and parameters.
        """
        pass

    @property
    def json(self):
        """a `dict` that can be serialized as semantic SQuaSH json."""
        blobIds = list(set([b.identifier for b in self._linkedBlobs]))
        object_doc = {'metric': self.metric,
                      'value': self.value,
                      'parameters': self.parameters,
                      'blobs': blobIds,
                      'schema': self.schema,
                      'spec_name': self.specName,
                      'filter': self.bandpass}
        json_doc = JsonSerializationMixin.jsonify_dict(object_doc)
        return json_doc

    def checkSpec(self, name):
        """Check this measurement against a specification level `name`, of the
        metric.

        Internally this method retrieves the Specification object, filtering
        first by the `name`, but also by this object's `bandpass` attribute
        if specifications are bandpass-dependent.
        """
        return self.metric.checkSpec(self.value, name, bandpass=self.bandpass)


class BlobBase(JsonSerializationMixin):
    """Baseclass for Blob classes. Blobs are flexible containers of data
    that are serialized to JSON.
    """

    def __init__(self):
        self._id = uuid.uuid4().hex
        self._doc = {}

    @abc.abstractproperty
    def schema(self):
        """A `str` identify the schema of this blob."""
        pass

    @property
    def identifier(self):
        return self._id

    @property
    def json(self):
        json_doc = JsonSerializationMixin.jsonify_dict(self._doc)
        return json_doc

    def __getitem__(self, key):
        """Access Blob members by key."""
        return self._doc[key]


class Job(JsonSerializationMixin):
    """A Job is a wrapper around all measurements and blob metadata associated
    with a validate_drp run.

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
        m : :class:`lsst.validate.drp.base.MeasurementBase`-type object
            A measurement object.
        """
        assert isinstance(m, MeasurementBase)
        if m.identifier not in self._measurement_ids:
            self._measurements.append(m)
            self._measurement_ids.add(m.identifier)
            for b in m.blobs:
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
        b : :class:`lsst.validate.drp.base.BlobBase`-type object
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
