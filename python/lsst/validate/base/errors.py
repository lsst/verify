# See COPYRIGHT file at the top of the source tree.
"""Exceptions for the lsst.validate namespace."""

__all__ = ['ValidateError', 'ValidateErrorNoStars',
           'ValidateErrorSpecification',
           'ValidateErrorUnknownSpecificationLevel']


class ValidateError(Exception):
    """Base classes for exceptions in validate_base."""
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
