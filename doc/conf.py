#!/usr/bin/env python
"""Sphinx configurations to build package documentation."""

from documenteer.sphinxconfig.stackconf import build_package_configs

import lsst.verify


globals().update(build_package_configs(
    project_name='verify',
    version=lsst.verify.version.__version__,
    doxygen_xml_dirname=None))

# DEBUG only
automodsumm_writereprocessed = False
