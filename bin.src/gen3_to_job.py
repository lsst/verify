#!/usr/bin/env python
import argparse

from lsst.verify.bin.jobReporter import main


if __name__ == "__main__":
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
        '--metrics_package', type=str, default="validate_drp",
        help='Name of metrics package to load')
    parser.add_argument(
        '--spec', type=str, default="design",
        help='Spec level to apply: minimum, design, or stretch')
    parser.add_argument(
        '--dataset_name', type=str,
        default="validation_data_hsc",
        help='Name of the dataset for which the report is being generated.')

    args = parser.parse_args()
    main(args.repository,
         args.collection,
         args.metrics_package,
         args.spec,
         args.dataset_name)
