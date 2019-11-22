# This file is part of verify.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Shared code for persisting verify objects to YAML.

The YAML code is centralized in one module to simplify registration code.
"""

__all__ = []  # code defined by this module only called indirectly


import astropy.units as u
import yaml

from .measurement import Measurement


def _getValidLoaders():
    """Return a list of supported YAML loaders.

    For YAML >= 5.1 need a different Loader for the constructor

    Returns
    -------
    loaderList : `sequence`
        A list of loaders that are supported by the current PyYAML version.
    """
    loaderList = [yaml.Loader, yaml.CLoader]
    try:
        loaderList.append(yaml.FullLoader)
    except AttributeError:
        pass
    try:
        loaderList.append(yaml.UnsafeLoader)
    except AttributeError:
        pass
    try:
        loaderList.append(yaml.SafeLoader)
    except AttributeError:
        pass
    return loaderList


def _registerTypes():
    yaml.add_representer(Measurement, measurement_representer)

    for loader in _getValidLoaders():
        yaml.add_constructor(
            "lsst.verify.Measurement", measurement_constructor, Loader=loader)


# Based on Measurement.json, but provides self-contained representation
def measurement_representer(dumper, measurement):
    """Persist a Measurement as a mapping.
    """
    if measurement.quantity is None:
        normalized_value = None
        normalized_unit_str = None
    elif measurement.metric is not None:
        # ensure metrics are normalized to metric definition's units
        metric = measurement.metric
        normalized_value = measurement.quantity.to(metric.unit).value
        normalized_unit_str = metric.unit_str
    else:
        normalized_value = measurement.quantity.value
        normalized_unit_str = str(measurement.quantity.unit)

    return dumper.represent_mapping(
        "lsst.verify.Measurement",
        {"metric": str(measurement.metric_name),
         "identifier": measurement.identifier,
         "value": normalized_value,
         "unit": normalized_unit_str,
         },
    )


# Based on Measurement.deserialize
def measurement_constructor(loader, node):
    state = loader.construct_mapping(node)

    quantity = u.Quantity(state["value"], u.Unit(state["unit"]))

    instance = Measurement(state["metric"], quantity=quantity)
    instance._id = state["identifier"]  # re-wire id from serialization
    return instance


_registerTypes()
