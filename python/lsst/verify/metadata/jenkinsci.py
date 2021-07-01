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
__all__ = ['get_jenkins_env']

import os


def get_jenkins_env():
    """Gather metadata entries from LSST DM Jenkins CI environment.

    Returns
    -------
    prov : `dict`
        Dictionary of metadata items obtained from the Jenkins CI
        environment. Fields are:

        - ``'ci_id'``: Job ID in Jenkins CI.
        - ``'ci_name'``: Job name in Jenkins CI.
        - ``'ci_dataset'``: Name of the dataset being processed.
        - ``'ci_label'``: Value of ``${label}`` environment variable in
          Jenkins CI.
        - ``'ci_url'``: URL to job page in Jenkins CI.
        - ``'ci_refs'``: whitespace-delimited branch references
        - ``'status'``: Job return status (always ``0``).

    Examples
    --------
    This metadata is intended to be inserted into a job's metadata:

    >>> from lsst.verify import Job
    >>> job = Job()
    >>> job.meta.update(get_jenkins_env())
    """

    return {
        'ci_id': os.getenv('BUILD_ID', 'unknown'),
        'ci_name': os.getenv('PRODUCT', 'unknown'),
        'ci_dataset': os.getenv('dataset', 'unknown'),
        'ci_label': os.getenv('label', 'unknown'),
        'ci_refs': os.getenv('refs', 'unknown'),
        'ci_url': os.getenv('BUILD_URL', 'https://example.com'),
        'status': 0,
    }
