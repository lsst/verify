# See COPYRIGHT file at the top of the source tree.

try:
    # validate_base does not formally use on lsstimport, but we still attempt
    # to import it for compatiblity with the lsst.validate Stack.
    import lsstimport
except ImportError:
    pass
import pkgutil
__path__ = pkgutil.extend_path(__path__, __name__)
