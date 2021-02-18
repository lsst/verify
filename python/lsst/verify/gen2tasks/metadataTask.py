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

__all__ = ["SquashMetadataTask"]

from lsst.pex.config import Config
from lsst.pipe.base import Task, Struct


class SquashMetadataTask(Task):
    """A Task for adding SQuaSH-required metadata to a Job.

    This task is intended as a subtask of `MetricsControllerTask`.
    """

    _DefaultName = "squashMetadata"
    ConfigClass = Config

    @staticmethod
    def _getInstrument(dataref):
        """Extract the instrument name associated with a Butler dataset.

        Parameters
        ----------
        dataref : `lsst.daf.persistence.ButlerDataRef`
            A data reference to any dataset of interest.

        Returns
        -------
        instrument : `str`
            The canonical name of the instrument, in all uppercase form.
        """
        camera = dataref.get('camera')
        instrument = camera.getName()
        return instrument.upper()

    def run(self, job, *, dataref, **kwargs):
        """Add metadata to a Job object.

        Parameters
        ----------
        job : `lsst.verify.Job`
            The job to be instrumented with metadata. The input object will be
            modified by this call.
        dataref : `lsst.daf.persistence.ButlerDataRef`
            The data reference associated with the job.
        kwargs
            Additional keyword arguments. These exist to support duck-typing
            with tasks that require different inputs, and are unused.

        Returns
        -------
        struct : `lsst.pipe.base.Struct`
            A `~lsst.pipe.base.Struct` containing the following component:

            ``job``
                a reference to the input `~lsst.verify.Job`.

        Notes
        -----
        The current implementation adds the following metadata:

        ``"instrument"``
            The canonical name of the instrument, in all
            uppercase form (`str`).
        ``[data ID key]``
            One metadata key for each key in ``dataref``'s data ID
            (e.g., ``"visit"``), with the corresponding value.
        """
        job.meta['instrument'] = SquashMetadataTask._getInstrument(dataref)
        job.meta['butler_generation'] = 'Gen2'
        job.meta.update(dataref.dataId)

        return Struct(job=job)
