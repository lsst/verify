# See COPYRIGHT file at the top of the source tree.
"""Exceptions for the lsst.verify namespace."""

__all__ = ['VerifyError',
           'VerifySpecificationError',
           'SpecificationResolutionError']


class VerifyError(Exception):
    """Base error for verify."""
    pass


class VerifySpecificationError(VerifyError):
    """Error accessing or using requirement specifications."""
    pass


class SpecificationResolutionError(Exception):
    """Error resolving a specification document's stated inheritance."""
    pass
