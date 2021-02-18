#!/usr/bin/env python

from lsst.verify.bin.jobReporter import main, build_argparser


if __name__ == "__main__":
    parser = build_argparser()
    args = parser.parse_args()
    main(args.repository,
         args.collection,
         args.metrics_package,
         args.spec,
         args.dataset_name)
