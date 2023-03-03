# This file is part of verify.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Tools for loading metric values from a butler and printing them, or from
two butlers and differencing them.

These functions are used by the
:doc:`print_metricvalues <scripts/print_metricvalues>` script.
"""
__all__ = ["load_value", "load_timing", "load_memory",
           "print_metrics", "print_diff_metrics", "load_from_butler"]

import astropy.units as u


def print_metrics(butler, kind, *, data_id_keys=None,
                  data_id_restriction=None, verbose=False):
    """Print all metrics with measured values in the given repo.

    Parameters
    ----------
    butler : `lsst.daf.butler.Butler`
        Butler to load values from.
    kind : `str`
        Kind of metrics to load.
    data_id_keys : `collection` [`str`], optional
        List of Butler dataId keys to restrict the printed output to;
        for example: ``("detector", "visit")``.
    data_id_restriction : `dict`, optional
        Only include values whose dataId matches these key:value pairs;
        for example: ``{"detector": 50}``. If a metric does not use a key, it
        is not included.
    verbose : `bool`, optional
        Print extra information when loading values.

    Returns
    -------
    output : `str`
        A formatted string with all the requested metric values.
    """
    def value_formatter_default(value):
        return f"{value}"

    def value_formatter_timing(value):
        return f"{value.datum.label}: {value.quantity:.4}"

    def value_formatter_memory(value):
        return f"{value.datum.label}: {value.quantity.to(u.Mibyte):.5}"

    match kind:
        case "value":
            result = load_value(butler, verbose=verbose)
            value_formatter = value_formatter_default
        case "timing":
            result = load_timing(butler, verbose=verbose)
            value_formatter = value_formatter_timing
        case "memory":
            result = load_memory(butler, verbose=verbose)
            value_formatter = value_formatter_memory
        case _:
            raise RuntimeError(f"Cannot handle kind={kind}")

    old_data_id = None
    for (data_id, metric), value in sorted(result.items()):
        if not _match_data_id(data_id, data_id_restriction):
            continue
        if old_data_id != data_id:
            print(f"\n{_data_id_label(data_id, data_id_keys)}")
            old_data_id = data_id

        print(value_formatter(value))


def print_diff_metrics(butler1, butler2, data_id_keys=None, verbose=False):
    """Load metric values from two repos and print their differences.

    This only supports differencing metrics that aren't time or memory-related.

    Parameters
    ----------
    butler1, butler2 : `lsst.daf.butler.Butler`
        Butlers to load values to difference from.
    data_id_keys : `collection` [`str`], optional
        List of Butler dataId keys to restrict the printed output to;
        for example: ``("detector", "visit")``. If a metric does not use all of
        of these keys, it is printed with default formatting.
    verbose : `bool`, optional
        Print extra information when loading values, and about failures.
    """
    result1 = load_value(butler1)
    result2 = load_value(butler2)

    same = 0
    failed = 0
    old_data_id = None
    for key in sorted(result1):
        data_id, metric = key
        if old_data_id != data_id:
            print(f"\n{_data_id_label(data_id, data_id_keys)}")
            old_data_id = data_id

        try:
            value1 = result1[key]
            value2 = result2[key]
        except KeyError:
            print(f"Result 2 does not contain metric '{metric}'")
            failed += 1
            continue

        delta = value2.quantity - value1.quantity
        if delta != 0 or verbose:
            print(f"{value1.datum.label}: {delta} / {value1.quantity}")
        if delta == 0:
            same += 1

    print(f"Number of metrics that are the same in both runs: {same} / {len(result2)}")

    if failed != 0:
        keys1 = sorted(list(result1.keys()))
        keys2 = sorted(list(result2.keys()))
        print()
        print(f"butler1 metrics found: {len(result1)}")
        print(f"butler2 metrics found: {len(result2)}")
        print(f"metrics in butler1 that were not found in butler2: {failed}")
        print("Check that the butler registry schemas are comparable, if most metrics are not being found.")
        print("Run with verbose mode (-v) for more info.")
        if verbose:
            print("Full DataCoordinates for the first key of each result, to compare schemas:")
            print(keys1[0][0].full)
            print(keys2[0][0].full)


def _match_data_id(data_id, data_id_restriction):
    """Return True if ``data_id`` matches a non-None ``data_id_restriction``.
    """
    if data_id_restriction is None:
        return True
    for key, value in data_id_restriction.items():
        if key not in data_id or (data_id[key] != value):
            return False
    return True


def _data_id_label(data_id, keys):
    """Return a string label for this data_id, optionally restricting the
    output to only certain key:value pairs.

    If any of the specified keys are not in the data_id, this will return the
    default data_id formatting.
    """
    if keys is None:
        return data_id

    if not set(keys).issubset(set(data_id)):
        return data_id

    return ', '.join(f"{key}: {data_id[key]}" for key in keys)


def load_value(butler, verbose=False):
    """Load all measured non-time/non-memory metrics in the given butler repo.

    Parameters
    ----------
    butler : `lsst.daf.butler.Butler`
        Butler to load values from.
    verbose : `bool`, optional
        Print extra information when loading values.

    Returns
    -------
    result : `dict` [`tuple`, `MetricValue`]
        The loaded metric values, keyed on data_id
        (`~lsst.daf.butler.DataCoordiate`) and metric name (`str`).
    """
    return load_from_butler(butler, "metricvalue*", reject_suffix=("Time", "Memory"), verbose=verbose)


def load_timing(butler, verbose=False):
    """Load all measured timing metrics in the given butler repo.

    Parameters
    ----------
    butler : `lsst.daf.butler.Butler`
        Butler to load values from.
    verbose : `bool`, optional
        Print extra information when loading values.

    Returns
    -------
    result : `dict` [`tuple`, `MetricValue`]
        The loaded metric values, keyed on data_id
        (`~lsst.daf.butler.DataCoordiate`) and metric name (`str`).
    """
    return load_from_butler(butler, "metricvalue*Time", verbose=verbose)


def load_memory(butler, verbose=False):
    """Load all measured memory usage metrics in the given butler repo.

    Parameters
    ----------
    butler : `lsst.daf.butler.Butler`
        Butler to load values from.
    verbose : `bool`, optional
        Print extra information when loading values.

    Returns
    -------
    result : `dict` [`tuple`, `MetricValue`]
        The loaded metric values, keyed on data_id
        (`~lsst.daf.butler.DataCoordiate`) and metric name (`str`).
    """
    return load_from_butler(butler, "metricvalue*Memory", verbose=verbose)


def load_from_butler(butler, query, reject_suffix=None, verbose=False):
    """
    Parameters
    ----------
    butler : `lsst.daf.butler.Butler`
        Butler created with the appropriate collections, etc.
    query : `str`
        Butler dataset query to get the metric names to load.
    reject_suffix : `str` or `iterable`, optional
        String or tuple of strings to not load if they appear at the end of
        the metric name.
    verbose : bool, optional
        Print extra information when loading.

    Returns
    -------
    result : `dict` [`tuple`, `MetricValue`]
        The loaded metric values, keyed on data_id
        (`~lsst.daf.butler.DataCoordiate`) and metric name (`str`).
    """
    # all possible metrics that have been registered
    metrics = list(butler.registry.queryDatasetTypes(query))
    if reject_suffix is not None:
        metrics = [m for m in metrics if not m.name.endswith(reject_suffix)]

    result = {}
    data_ids = set()
    for metric in metrics:
        # We only want one of each, so we need findFirst.
        datasets = set(butler.registry.queryDatasets(metric, findFirst=True))
        for dataset in datasets:
            value = butler.get(dataset)
            data_ids.add(dataset.dataId)
            result[(dataset.dataId, metric.name)] = value

    if verbose:
        print(f"Loaded {len(result)} values for {len(data_ids)} dataIds and {len(metrics)} metrics.")
    return result
