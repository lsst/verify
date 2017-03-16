# See COPYRIGHT file at the top of the source tree.
"""Tools for building and parsing fully-qualified names of metrics and
specifications.
"""
from __future__ import print_function

__all__ = ['Name']


class Name(object):
    """Semantic name of a metric or specification in the lsst.verify framework.
    """

    def __init__(self, package=None, metric=None, spec=None):
        self.package = package
        self.metric = metric
        self.spec = spec

    @property
    def has_package(self):
        """`True` if this object contains a package name (`bool`)."""
        if self.package is not None:
            return True
        else:
            return False

    @property
    def has_spec(self):
        """`True` if this object contains a specification name, either
        relative or fully-qualified (`bool`).
        """
        if self.spec is not None:
            return True
        else:
            return False

    @property
    def has_metric(self):
        """`True` if this object contains a metric name, either
        relative or fully-qualified (`bool`).
        """
        if self.metric is not None:
            return True
        else:
            return False

    @property
    def has_relative(self):
        """`True` if a relative specification name can be formed from this
        object, i.e., `metric` and `spec` attributes are set (`bool`).
        """
        if self.is_spec and self.has_metric:
            return True
        else:
            return False

    @property
    def is_package(self):
        """`True` if this object is a package name (`bool`)."""
        if self.has_package and \
                self.is_metric is False and \
                self.is_spec is False:
            return True
        else:
            return False

    @property
    def is_metric(self):
        """`True` if this object is a metric name, either relative or
        fully-qualified (`bool`).
        """
        if self.has_metric is True and self.has_spec is False:
            return True
        else:
            return False

    @property
    def is_spec(self):
        """`True` if this object is a specification name, either relative or
        fully-qualified (`bool`).
        """
        if self.has_spec is True:
            return True
        else:
            return False

    @property
    def is_fq(self):
        """`True` if this object is a fully-qualified name of either a
        package, metric or specification (`bool`).

        Examples:

        - ``'validate_drp'`` is a fully-qualified package name.
        - ``'validate_drp.PA1'`` is a fully-qualified metric name.
        - ``'validate_drp.PA1.design_gri'`` is a fully-qualified specification
          name.
        """
        if self.is_package:
            # package names are by definition fully qualified
            return True
        elif self.is_metric and self.has_package:
            # fully-qualified metric
            return True
        elif self.is_spec and self.has_package and self.has_metric:
            # fully-qualified specification
            return True
        else:
            return False

    @property
    def is_relative(self):
        """`True` if this object is a specification name that's not
        fully-qualified, but is relative to a metric name (`bool`).
        relative to a base name. (`bool`).

        For example, ``PA1.design_gri`` is a relative specification name.

        Package and metric names are never relative.
        """
        if self.is_spec and \
                self.has_metric is True and \
                self.has_package is False:
            return True
        else:
            return False

    def __repr__(self):
        if self.is_package:
            return 'Name({self.package!r})'.format(self=self)
        elif self.is_metric and not self.is_fq:
            return 'Name(metric={self.metric!r})'.format(self=self)
        elif self.is_metric and self.is_fq:
            return 'Name({self.package!r}, {self.metric!r})'.format(
                self=self)
        elif self.is_spec and not self.is_fq and not self.is_relative:
            return 'Name(spec={self.spec!r})'.format(
                self=self)
        elif self.is_spec and not self.is_fq and self.is_relative:
            return 'Name(metric={self.metric!r}, spec={self.spec!r})'.format(
                self=self)
        else:
            # Should be a fully-qualified specification
            template = 'Name({self.package!r}, {self.metric!r}, {self.spec!r})'
            return template.format(self=self)

    def __str__(self):
        if self.is_package:
            return self.package
        elif self.is_metric and not self.is_fq:
            return self.metric
        elif self.is_metric and self.is_fq:
            return '{self.package}.{self.metric}'.format(self=self)
        elif self.is_spec and not self.is_fq and not self.is_relative:
            return self.spec
        elif self.is_spec and not self.is_fq and self.is_relative:
            return '{self.metric}.{self.spec}'.format(self=self)
        else:
            # Should be a fully-qualified specification
            return '{self.package}.{self.metric}.{self.spec}'.format(
                self=self)

    @property
    def fqn(self):
        """The fully-qualified name (`str`).

        Raises
        ------
        AttributeError
           If the name is not a fully-qualified name (check `is_fq`)
        """
        if self.is_fq:
            return str(self)
        else:
            message = '{self!r} is not a fully-qualified name'
            raise AttributeError(message.format(self=self))

    @property
    def relative_name(self):
        """The relative specification name (`str`).

        Raises
        ------
        AttributeError
           If the object does not represent a specification, or if a relative
           name cannot be formed because the `metric` is None.
        """
        if self.has_relative:
            return '{self.metric}.{self.spec}'.format(self=self)
        else:
            message = '{self!r} is not a relative specification name'
            raise AttributeError(message.format(self=self))
