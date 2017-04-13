# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import operator

import astropy.units as u
from astropy.tests.helper import quantity_allclose

from ..jsonmixin import JsonSerializationMixin
from ..datum import Datum
from ..naming import Name
from .base import Specification


__all__ = ['ThresholdSpecification']


class ThresholdSpecification(Specification):
    """A threshold-type specification, associated with a `Metric`, that
    defines a binary comparison against a measurement.

    Parameters
    ----------
    name : `str`
        Name of the specification for a metric. LPM-17, for example,
        uses ``'design'``, ``'minimum'`` and ``'stretch'`` terminology.
    quantity : `astropy.units.Quantity`
        The specification threshold level.
    operator_str : `str`
        The threshold's binary comparison operator. The operator is oriented
        so that ``measurement {{ operator }} threshold quantity`` is the
        specification test. Can be one of: ``'<'``, ``'<='``, ``'>'``,
        ``'>='``, ``'=='``, or ``'!='``.
    kwargs : `dict`
        Keyword arguments passed directly to the
        `lsst.validate.base.Specification` constructor.

    Raises
    ------
    TypeError
        If ``name`` is not compartible with `~lsst.verify.Name`,
        or `threshold` is not a `~astropy.units.Quantity`, or if the
        ``operator_str`` cannot be converted into a Python binary comparison
        operator.
    """

    threshold = None
    """The specification threshold level (`astropy.units.Quantity`)."""

    def __init__(self, name, threshold, operator_str, **kwargs):
        Specification.__init__(self, name, **kwargs)

        self.threshold = threshold
        if not isinstance(self.threshold, u.Quantity):
            message = 'threshold {0!r} must be an astropy.units.Quantity'
            raise TypeError(message.format(self.threshold))
        if not self.threshold.isscalar:
            raise TypeError('threshold must be scalar')

        try:
            self.operator_str = operator_str
        except ValueError:
            message = '{0!r} is not a known operator'.format(operator_str)
            raise TypeError(message)

    @property
    def type(self):
        return 'threshold'

    def __eq__(self, other):
        return (self.type == other.type) and \
            (self.name == other.name) and \
            quantity_allclose(self.threshold, other.threshold) and \
            (self.operator_str == other.operator_str)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "ThresholdSpecification({0!r}, {1!r}, {2!r})".format(
            self.name,
            self.threshold,
            self.operator_str)

    @property
    def datum(self):
        """Representation of this `ThresholdSpecification`\ 's threshold as
        a `Datum`.
        """
        return Datum(self.threshold, label=str(self.name))

    @classmethod
    def from_json(cls, json_data):
        """Construct a `ThresholdSpecification` from a JSON document.

        Parameters
        ----------
        json_data : `dict`
            ThresholdSpecification JSON object.

        Returns
        -------
        specification : `ThresholdSpecification`
            ThresholdSpecification from JSON.
        """
        q = Datum._rebuild_quantity(
            json_data['threshold']['value'],
            json_data['threshold']['unit'])
        s = cls(name=json_data['name'],
                threshold=q,
                operator_str=json_data['threshold']['operator'])
        return s

    @classmethod
    def deserialize(cls, name=None, threshold=None,
                    metric=None, package=None, **kwargs):
        """Deserialize from keys in a specification YAML document or a
        JSON serialization into a `ThresholdSpecification` instance.

        Parameters
        ----------
        name : `str` or `lsst.validate.base.Name`
            Specification name, either as a string or
            `~lsst.validate.base.Name`.
        threshold : `dict`
            A `dict` with fields:

            - ``'value'``: threshold value (`float` or `int`).
            - ``'unit'``: threshold unit, as an `astropy.units.Unit`-
              compatible `str`.
            - ``'operator'``: a binary comparison operator, described in
              the class parameters documentation (`str`).
        metric : `str` or `lsst.validate.base.Name`, optional
            Name of the fully-qualified name of the metric the specification
            corresponds to. This parameter is optional if ``name`` is already
            fully-qualified.
        package : `str` or `lsst.validate.base.Name`, optional
            Name of the package the specification corresponds to. This
            parameter is optional if ``name`` or ``metric`` are already
            fully-qualified.
        kwargs : `dict`
            Keyword arguments passed directly to the
            `lsst.validate.base.Specification` constructor.

        Returns
        -------
        specification : `ThresholdSpecification`
            A specification instance.
        """
        _name = Name(metric=metric, spec=name)
        operator_str = threshold['operator']
        _threshold = u.Quantity(threshold['value'],
                                u.Unit(threshold['unit']))
        return cls(_name, _threshold, operator_str, **kwargs)

    def _serialize_type(self):
        """Serialize attributes of this specification type to a `dict` that is
        JSON-serializable.
        """
        return JsonSerializationMixin.jsonify_dict(
            {
                'value': self.threshold.value,
                'unit': self.threshold.unit.to_string(),
                'operator': self.operator_str
            }
        )

    @property
    def operator_str(self):
        """Threshold comparision operator ('str').

        A measurement *passes* the specification if::

           measurement {{ operator }} threshold == True

        The operator string is a standard Python binary comparison token, such
        as: ``'<'``, ``'>'``, ``'<='``, ``'>='``, ``'=='`` or ``'!='``.
        """
        return self._operator_str

    @operator_str.setter
    def operator_str(self, v):
        # Cache the operator function as a means of validating the input too
        self._operator = ThresholdSpecification.convert_operator_str(v)
        self._operator_str = v

    @property
    def operator(self):
        """Binary comparision operator that tests success of a measurement
        fulfilling a specification of this metric.

        Measured value is on left side of comparison and specification level
        is on right side.
        """
        return self._operator

    @staticmethod
    def convert_operator_str(op_str):
        """Convert a string representing a binary comparison operator to
        the operator function itself.

        Operators are oriented so that the measurement is on the left-hand
        side, and specification threshold on the right hand side.

        The following operators are permitted:

        ========== =============
        ``op_str`` Function
        ========== =============
        ``>=``     `operator.ge`
        ``>``      `operator.gt`
        ``<``      `operator.lt`
        ``<=``     `operator.le`
        ``==``     `operator.eq`
        ``!=``     `operator.ne`
        ========== =============

        Parameters
        ----------
        op_str : `str`
            A string representing a binary operator.

        Returns
        -------
        op_func : obj
            An operator function from the `operator` standard library
            module.

        Raises
        ------
        ValueError
            Raised if ``op_str`` is not a supported binary comparison operator.
        """
        operators = {'>=': operator.ge,
                     '>': operator.gt,
                     '<': operator.lt,
                     '<=': operator.le,
                     '==': operator.eq,
                     '!=': operator.ne}
        try:
            return operators[op_str]
        except KeyError:
            message = '{0!r} is not a supported threshold operator'.format(
                op_str)
            raise ValueError(message)

    def check(self, measurement):
        """Check if a measurement passes this specification.

        Parameters
        ----------
        measurement : `astropy.units.Quantity`
            The measurement value. The measurement `~astropy.units.Quantity`
            must have units *compatible* with `threshold`.

        Returns
        -------
        passed : `bool`
            `True` if the measurement meets the specification,
            `False` otherwise.

        Raises
        ------
        astropy.units.UnitError
            Raised if the measurement cannot be compared to the threshold.
            For example, if the measurement is not an `astropy.units.Quantity`
            or if the units are not compatible.
        """
        return self.operator(measurement, self.threshold)
