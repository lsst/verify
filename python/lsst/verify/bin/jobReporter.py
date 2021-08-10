import argparse
import json

from lsst.verify import Job, MetricSet
from lsst.daf.butler import Butler, FileTemplate


__all__ = ["main", "JobReporter", "build_argparser"]


def build_argparser():
    desc = 'Produce a Job object which can either be used ' \
           'to build a local report or to ship to SQuaSH.'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        'repository', type=str,
        help='Path to a valid gen3 repository')
    parser.add_argument(
        'collection', type=str,
        help='Collection to search for metric measurement values')
    parser.add_argument(
        '--metrics_package', type=str,
        help='Metrics namespace to filter by. If omitted, all metrics '
             'are processed.')
    parser.add_argument(
        '--spec', type=str, default="design",
        help='Spec level to apply: minimum, design, or stretch')
    parser.add_argument(
        '--dataset_name', type=str, required=True,
        help='Name of the dataset for which the report is being generated.'
             'This is the desired ci_dataset tag in SQuaSH.')
    return parser


def main(repository, collection, metrics_package, spec, dataset_name):
    """Extract metric values from a Gen 3 repository and rewrite them to disk
    in Job format.

    Parameters
    ----------
    Parameters are the same as for the `JobReporter` class.
    """
    jr = JobReporter(repository,
                     collection,
                     metrics_package,
                     spec,
                     dataset_name)
    jobs = jr.run()
    if len(jobs) == 0:
        raise RuntimeError('Job reporter returned no jobs.')
    for k, v in jobs.items():
        filename = f"{metrics_package or 'all'}_{spec}_{k}.verify.json"
        with open(filename, 'w') as fh:
            json.dump(v.json, fh, indent=2, sort_keys=True)


def make_key(ref):
    names = sorted(list(ref.dataId.names))
    names.append('run')  # "run" must be in the template
    key_tmpl = '_'.join(['{' + el + '}' for el in names])
    file_tmpl = FileTemplate(key_tmpl)
    key = file_tmpl.format(ref)
    return key


class JobReporter:
    """A class for extracting metric values from a Gen 3 repository and
    repackaging them as Job objects.

    Parameters
    ----------
    repository : `str`
        Path to a Butler configuration YAML file or a directory containing one.
    collection : `str`
        Name of the collection to search for metric values.
    metrics_package : `str` or `None`
        If provided, the namespace by which to filter selected metrics.
    spec : `str`
        The level of specification to filter metrics by.
    dataset_name : `str`
        The name of the dataset to report to SQuaSH through the
        ``ci_dataset`` tag.
    """

    def __init__(self,
                 repository,
                 collection,
                 metrics_package,
                 spec,
                 dataset_name):
        # Hard coding verify_metrics as the packager for now.
        # It would be easy to pass this in as an argument, if necessary.
        self.metrics = MetricSet.load_metrics_package(
            package_name_or_path='verify_metrics',
            subset=metrics_package)
        self.butler = Butler(repository)
        self.registry = self.butler.registry
        self.spec = spec
        self.collection = collection
        self.dataset_name = dataset_name

    def run(self):
        """Collate job information.

        Returns
        -------
        jobs : `dict` [`str`, `lsst.verify.Job`]
            A mapping of `~lsst.verify.Job` objects, indexed by a string
            representation of their data ID.
        """
        jobs = {}
        for metric in self.metrics:
            dataset = f'metricvalue_{metric.package}_{metric.metric}'
            datasetRefs = list(self.registry.queryDatasets(
                dataset,
                collections=self.collection,
                findFirst=True))
            for ref in datasetRefs:
                m = self.butler.get(ref, collections=self.collection)
                # make the name the same as what SQuaSH Expects
                m.metric_name = metric

                # queryDatasets guarantees ref.dataId.hasFull()
                dataId = ref.dataId.full.byName()
                key = make_key(ref)

                # For backward-compatibility with Gen 2 SQuaSH uploads
                pfilt = dataId.get('physical_filter')
                if not pfilt:
                    # Grab the physical filter associated with the abstract
                    # filter. In general there may be more than one. Take the
                    # shortest assuming it is the most generic.
                    pfilts = [el.name for el in
                              self.registry.queryDimensionRecords(
                                  'physical_filter',
                                  dataId=ref.dataId)]
                    pfilt = min(pfilts, key=len)

                if key not in jobs.keys():
                    job_metadata = {
                        'filter': pfilt,
                        'butler_generation': 'Gen3',
                        'ci_dataset': self.dataset_name,
                    }
                    job_metadata.update(dataId)
                    # Get dataset_repo_url from repository somehow?
                    jobs[key] = Job(meta=job_metadata, metrics=self.metrics)
                jobs[key].measurements.insert(m)
        return jobs
