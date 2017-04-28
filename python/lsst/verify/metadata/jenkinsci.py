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
from __future__ import print_function

__all__ = ['get_jenkins_env']

import datetime
import os


def get_jenkins_env():
    """Gather metadata entries from LSST DM Jenkins CI environment.

    Returns
    -------
    prov : `dict`
        Dictionary of metadata items obtained from the Jenkins CI
        environment. Fields are:

        - ``'date'``: ISO8601-formatted current datetime.
        - ``'ci_id'``: Job ID in Jenkins CI.
        - ``'ci_name'``: Job name in Jenkins CI.
        - ``'ci_dataset'``: Name of the dataset being processed.
        - ``'ci_label'``: Value of ``${label}`` environment variable in
          Jenkins CI.
        - ``'ci_url'``: URL to job page in Jenkins CI.
        - ``'status'``: Job return status (always ``0``).

    Examples
    --------
    This metadata is intended to be inserted into a job's metadata:

    >>> from lsst.verify import Job
    >>> job = Job()
    >>> job.meta.update(get_jenkins_env())
    """
    utc = UTC()

    return {
        'date': datetime.datetime.now(utc).isoformat(),
        'ci_id': os.getenv('BUILD_ID', 'unknown'),
        'ci_name': os.getenv('PRODUCT', 'unknown'),
        'ci_dataset': os.getenv('dataset', 'unknown'),
        'ci_label': os.getenv('label', 'unknown'),
        'ci_url': os.getenv('BUILD_URL', 'https://example.com'),
        'status': 0,
    }


class UTC(datetime.tzinfo):
    """UTC timezone."""
    # http://stackoverflow.com/a/2331635

    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta(0)
