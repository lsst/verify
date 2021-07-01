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
__all__ = ['get_ldf_env']

import os


def get_ldf_env():
    """Gather metadata entries from LSST Data Facility environment.

    Returns
    -------
    prov : `dict`
        Dictionary of metadata items obtained from the LDF environment.
        Fields are:

        - ``'dataset'``: the name of the dataset processed.
        - ``'dataset_repo_url'``: a reference URL with information about the
        dataset.
        - ``run_id``: ID of the run in the LDF environment.
        - ``run_id_url``: a reference URL with information about the run.
        - ``version_tag``: the version of the LSST stack used.

    Examples
    --------
    This metadata is intended to be inserted into a job's metadata:

    >>> from lsst.verify import Job
    >>> job = Job()
    >>> job.meta.update(get_ldf_env())
    """

    return {
        'dataset': os.getenv('DATASET', 'unknown'),
        'dataset_repo_url': os.getenv('DATASET_REPO_URL',
                                      'https://example.com'),
        'run_id': os.getenv('RUN_ID', 'unknown'),
        'run_id_url': os.getenv('RUN_ID_URL', 'https://example.com'),
        'version_tag': os.getenv('VERSION_TAG', 'unknown')
    }
