#!/usr/bin/env python
"""Sphinx configurations to build package documentation."""

from documenteer.sphinxconfig.stackconf import build_package_configs

import lsst.validate.base


_g = globals()
_g.update(build_package_configs(
    project_name='validate_base',
    copyright='2016 Association of Universities for '
              'Research in Astronomy, Inc.',
    version=lsst.validate.base.version.__version__,
    doxygen_xml_dirname=None))

intersphinx_mapping['astropy'] = ('http://docs.astropy.org/en/stable', None)

# DEBUG only
automodsumm_writereprocessed = False
