#
# LSST Data Management System
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# See COPYRIGHT file at the top of the source tree.
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
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <https://www.lsstcorp.org/LegalNotices/>.
#
"""API for parsing the manifest.txt file for EUPS packages found in lsstsw.
"""

__all__ = ['Manifest']

from collections import OrderedDict, namedtuple


ManifestItem = namedtuple('ManifestItem',
                          ['name', 'git_sha', 'version', 'dependencies'])


class Manifest(object):
    """Iterator over packages in lsstsw's manifest.txt dataset.

    Parameters
    ----------
    manifest_stream : file handle
        A file handle for `manifest.txt` (from `open`, for example).
    """

    def __init__(self, manifest_stream):
        self._build_id = None
        self._packages = OrderedDict()

        self._parse_manifest_stream(manifest_stream)

    def _parse_manifest_stream(self, manifest_stream):
        for manifest_line in manifest_stream.readlines():
            manifest_line = manifest_line.strip()
            if manifest_line.startswith('#'):
                continue
            elif manifest_line.startswith('BUILD'):
                self._build_id = manifest_line.split('=')[-1]
                continue
            parts = manifest_line.split()
            package_name = parts[0]
            git_commit = parts[1]
            eups_version = parts[2]
            if len(parts) == 4:
                deps = parts[3].split(',')
            else:
                deps = list()

            package = ManifestItem(
                name=package_name,
                git_sha=git_commit,
                version=eups_version,
                dependencies=deps)
            self._packages[package_name] = package

    def __iter__(self):
        """Iterate over package names.

        Yields
        ------
        name : `str`
            Package name.
        """
        for package in self._packages:
            yield package

    def items(self):
        """Iterate over packages.

        Yields
        ------
        item : `tuple`
            Tuple of ``(name, manifest_item)``. ``manifest_item`` is a
            `ManifestItem` (namedtuple) type with fields:

            - ``name``
            - ``git_sha``
            - ``version`` (EUPS version)
            - ``dependencies`` (list of EUPS package names)
        """
        for item in self._packages.items():
            yield item

    def __len__(self):
        """Count number of packages in the manifest (`int`)."""
        return len(self._packages)

    def __getitem__(self, package_name):
        """Get a package item from the manifest by name.

        Parameters
        ----------
        package_name : `str`
            EUPS package name.

        Returns
        -------
        item : `ManifestItem`
            `ManifestItem` is a `namedtuple` type with fields:

            - ``name``
            - ``git_sha``
            - ``version`` (EUPS version)
            - ``dependencies`` (list of EUPS package names)
        """
        return self._packages[package_name]

    def __contains__(self, package_name):
        """Test if a package is in the manifest.

        Parameters
        ----------
        package_name : `str`
            EUPS package name.

        Returns
        -------
        contained : `bool`
            `True` if package is in the manifest.
        """
        return package_name in self._packages

    @property
    def build(self):
        """Build number, bNNNN (`str`)."""
        return self._build_id
