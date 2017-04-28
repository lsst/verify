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
"""APIs for building software provenance from lsstsw."""

from __future__ import print_function

__all__ = ['LsstswRepos']

from past.builtins import basestring

import os

import yaml
try:
    # GitPython is an optional dependency, not part of the LSST Stack.
    import git
except ImportError:
    git = None


class LsstswRepos(object):
    """lsstsw package version information based on repos.yaml and
    checked out Git repositories.

    Parameters
    ----------
    dirname : `str`
        Path of an ``lsstsw`` directory.
    """
    def __init__(self, dirname):
        self._dirname = dirname
        self._repos = self._load_repos_yaml()

    def __contains__(self, package_name):
        """Test if a package is present in `lsstsw`'s repos.yaml dataset.
        """
        return package_name in self._repos

    def __len__(self):
        return len(self._repos)

    @property
    def manifest_path(self):
        """Path of the manifest.txt file."""
        return os.path.join(self._dirname, 'build', 'manifest.txt')

    def get_package_repo_path(self, package_name):
        """Path to a EUPS package repository in lsstsw/build.

        Parameters
        ----------
        package_name : `str`
            Name of the EUPS package.

        Returns
        -------
        path : `str`
            Directory path of the package's Git repository in lsstsw/build.
        """
        return os.path.join(self._dirname, 'build', package_name)

    def get_package_branch(self, package_name):
        """Get the name of the checked-out branch of an EUPS package cloned in
        lsstsw/build.

        Parameters
        ----------
        package_name : `str`
            Name of the EUPS package.

        Returns
        -------
        branch : `str`
            Name of the checked-out Git branch. If GitPython is not
            installed, `None` is always returned instead.
        """
        if git is not None:
            repo = git.Repo(self.get_package_repo_path(package_name))
            return repo.active_branch.name
        else:
            return None

    def get_package_commit_sha(self, package_name):
        """Get the hex SHA of the checked-out commit of an EUPS package
        cloned to lsstsw/build.

        Parameters
        ----------
        package_name : `str`
            Name of the EUPS package.

        Returns
        -------
        commit : `str`
            Hex SHA of the checkout-out Git commit. If GitPython is not
            installed, `None` is always returned instead.
        """
        if git is not None:
            repo = git.Repo(self.get_package_repo_path(package_name))
            return repo.active_branch.commit.hexsha
        else:
            return None

    def get_package_repo_url(self, package_name):
        """URL of the package's Git repository.

        This data is obtained from lsstsw/etc/repos.yaml.

        Parameters
        ----------
        package_name : `str`
            Name of the EUPS package.

        Returns
        -------
        repo_url : `str`
            Git origin URL of the package's Git repository.
        """
        s = self._repos[package_name]
        if isinstance(s, basestring):
            return s
        else:
            # For packages that have sub-documents, rather than the value
            # as the URL. See repos.yaml for format documentation.
            return s['url']

    def _load_repos_yaml(self):
        """Load lsstsw's repos.yaml."""
        yaml_path = os.path.join(self._dirname, 'etc', 'repos.yaml')
        with open(yaml_path) as f:
            repos = yaml.safe_load(f)
        return repos
