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


__all__ = ["make_test_butler", "make_dataset_type", "ref_from_connection",
           "run_quantum"]


from lsst.daf.butler import Butler, DatasetType, DataCoordinate, DatasetRef
from lsst.pipe.base import ButlerQuantumContext


# TODO: factor this out into a pipeline testing library
def make_test_butler(root, data_ids):
    """Create an empty repository with default configuration.

    Parameters
    ----------
    root : `str`
        The location of the root directory for the repository.
    data_ids : `dict` [`str`, `iterable` [`dict`]]
        A dictionary keyed by the dimensions used in the test. Each value
        is a dictionary of fields and values for that dimension. See
        :file:`daf/butler/config/dimensions.yaml` for required fields,
        listed as "keys" and "requires" under each dimension's entry.

    Returns
    -------
    butler : `lsst.daf.butler.Butler`
        A Butler referring to the new repository.
    """
    # TODO: takes 5 seconds to run; split up into class-level Butler
    #     with test-level runs after DM-21246
    Butler.makeRepo(root)
    butler = Butler(root, run="test")
    for dimension, values in data_ids.items():
        butler.registry.insertDimensionData(dimension, *values)
    return butler


def make_dataset_type(butler, name, dimensions, storageClass):
    """Create a dataset type in a particular repository.

    Parameters
    ----------
    butler : `lsst.daf.butler.Butler`
        The repository to update.
    name : `str`
        The name of the dataset type.
    dimensions : `set` [`str`]
        The dimensions of the new dataset type.
    storageClass : `str`
        The storage class the dataset will use.

    Returns
    -------
    dataset_type : `lsst.daf.butler.DatasetType`
        The new type.

    Raises
    ------
    ValueError
        Raised if the dimensions or storage class are invalid.
    ConflictingDefinitionError
        Raised if another dataset type with the same name already exists.
    """
    dataset_type = DatasetType(name, dimensions, storageClass,
                               universe=butler.registry.dimensions)
    butler.registry.registerDatasetType(dataset_type)
    return dataset_type


def ref_from_connection(butler, connection, data_id):
    """Create a DatasetRef for a connection in a collection.

    Parameters
    ----------
    butler : `lsst.daf.butler.Butler`
        The collection to point to.
    connection : `lsst.pipe.base.connectionTypes.DimensionedConnection`
        The connection defining the dataset type to point to.
    data_id : `Mapping` [`str`] or `lsst.daf.butler.DataCoordinate`
        The data ID for the dataset to point to.

    Returns
    -------
    ref : `lsst.daf.butler.DatasetRef`
        A reference to a dataset compatible with ``connection``, with ID
        ``data_id``, in the collection pointed to by ``butler``.
    """
    universe = butler.registry.dimensions
    data_id = DataCoordinate.standardize(data_id, universe=universe)
    return DatasetRef(
        datasetType=connection.makeDatasetType(universe),
        dataId=data_id,
    )


def run_quantum(task, butler, quantum):
    """Run a PipelineTask on a Quantum.

    Parameters
    ----------
    task : `lsst.pipe.base.PipelineTask`
        The task to run on the quantum.
    butler : `lsst.daf.butler.Butler`
        The collection to run on.
    quantum : `lsst.daf.butler.Quantum`
        The quantum to run.
    """
    butler_qc = ButlerQuantumContext(butler, quantum)
    connections = task.config.ConnectionsClass(config=task.config)
    input_refs, output_refs = connections.buildDatasetRefs(quantum)
    task.runQuantum(butler_qc, input_refs, output_refs)
