# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import operator
import yaml

from .jsonmixin import JsonSerializationMixin
from .datum import Datum
from .spec import Specification


__all__ = ['Metric']


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
    referencePage : str, optional
        Page where metric in defined in the reference document.

    Attributes
    ----------
    name : str
        Name of the metric
    description : str
        Short description of the metric.
    referenceDoc : str
        Name of the document that specifies this metric.
    referenceUrl : str
        URL of the document that specifies this metric.
    referencePage : int
        Page number in the document that specifies this metric.
    dependencies : dict
        A dictionary of named :class:`Datum` values that must be known when
        making a measurement against metric. Dependencies can be
        accessed as attributes of the specification object.
    operator : function
        Binary comparision operator that tests success of a measurement
        fulfilling a specification of this metric. Measured value is on
        left side of comparison and specification level is on right side.
    """
    def __init__(self, name, description, operatorStr, specs=None,
                 dependencies=None,
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

        if dependencies is None:
            self.dependencies = {}
        else:
            self.dependencies = dependencies

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
            A full metric YAML document loaded as a `dict`. Use this option
            to increase performance by eliminating redundant reads of a
            common metric YAML file. Alternatively, set `yamlPath`.
        yamlPath : str, optional
            The full path to a metrics.yaml file. Alternatively, set `yamlDoc`.
        resolveDependencies : bool, optional
            API users should always set this to `True`. The opposite is used
            only used internally.

        Raises
        ------
        RuntimeError
            Raised when neither `yamlDoc` or `yamlPath` are set.
        """
        if yamlDoc is None and yamlPath is not None:
            with open(yamlPath) as f:
                yamlDoc = yaml.load(f)
        elif yamlDoc is None and yamlPath is None:
            raise RuntimeError('Set either yamlDoc or yamlPath argument')
        metricDoc = yamlDoc[metricName]

        metricDeps = {}
        if 'dependencies' in metricDoc:
            for metricDepItem in metricDoc['dependencies']:
                name = metricDepItem.keys()[0]
                metricDepItem = dict(metricDepItem[name])
                v = metricDepItem['value']
                units = metricDepItem['units']
                d = Datum(v, units,
                          label=metricDepItem.get('label', None),
                          description=metricDepItem.get('description', None))
                metricDeps[name] = d

        m = cls(
            metricName,
            description=metricDoc.get('description', None),
            operatorStr=metricDoc['operator'],
            referenceDoc=metricDoc['reference'].get('doc', None),
            referenceUrl=metricDoc['reference'].get('url', None),
            referencePage=metricDoc['reference'].get('page', None),
            dependencies=metricDeps)

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

    def __getattr__(self, key):
        if key in self.dependencies:
            return self.dependencies[key]
        else:
            raise AttributeError("%r object has no attribute %r" %
                                 (self.__class__, key))

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
        refDoc = {
            'doc': self.referenceDoc,
            'page': self.referencePage,
            'url': self.referenceUrl}
        return JsonSerializationMixin.jsonify_dict({
            'name': self.name,
            'reference': refDoc,
            'description': self.description,
            'specifications': self.specs,
            'dependencies': self.dependencies})
