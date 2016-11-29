# See COPYRIGHT file at the top of the source tree.
"""Exceptions for the lsst.validate namespace."""

__all__ = ['ValidateError',
           'ValidateSpecificationError']


class ValidateError(Exception):
    """Base error for validate_base."""
    pass


class ValidateSpecificationError(ValidateError):
    """Error accessing or using requirement specifications."""
    pass
