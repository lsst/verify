from lsst.verify import Job, MetricSet
from lsst.daf.butler import Butler


class JobReporter:
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
        jobs = {}
        for metric in self.metrics:
            dataset = f'metricvalue_{metric.package}_{metric.metric}'
            data_ids = list(self.registry.queryDatasets(dataset,
                            collections=self.collection))
            for did in data_ids:
                m = self.butler.get(did, collections=self.collection)
                # make the name the same as what SQuaSH Expects
                m.metric_name = metric
                # Grab the physical filter associated with the abstract filter
                # In general there may be more than one.  Take the shortest
                # assuming it is the most generic.
                pfilts = [el.name for el in
                          self.registry.queryDimensionRecords(
                              'physical_filter',
                              dataId=did.dataId)]
                pfilt = min(pfilts, key=len)

                tract = did.dataId['tract']
                afilt = did.dataId['band']
                key = f"{tract}_{afilt}"
                if key not in jobs.keys():
                    job_metadata = {'instrument': did.dataId['instrument'],
                                    'filter': pfilt,
                                    'band': afilt,
                                    'tract': tract,
                                    'butler_generation': 'Gen3',
                                    'ci_dataset': self.dataset_name}
                    # Get dataset_repo_url from repository somehow?
                    jobs[key] = Job(meta=job_metadata, metrics=self.metrics)
                jobs[key].measurements.insert(m)
        return jobs
