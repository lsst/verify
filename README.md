# lsst.validate.base

**Measurement framework for performance metrics.**

Packages can use `lsst.validate.base` to report metric measurements to LSST Data Management's [SQUASH](https://squash.lsst.codes) dashboard.
This package is part of the [LSST Science Pipelines](https://pipelines.lsst.io).

`lsst.validate.base` provides:

- A schema for defining performance **metrics** (things that *can* be measured) and **specifications** (threshold values of a metric). The `lsst.validate.base.Metric` and `lsst.validate.base.Specification` classes provide Python access to metrics and specifications.
- An `lsst.validate.base.MeasurementBase` base class that can be inherited to make **measurement** classes. Measurement classes create well-structured self-describing datasets that track units, input datasets, and even measurement code parameters.
- An `lsst.validate.base.BlobBase` base class that can be inherited to make **blobs**: containers for semantically rich data.
- An `lsst.validate.base.Job` class that collects multiple measurements, their metrics, and blob datasets, and provides a JSON file that can be submitted to [SQUASH](https://squash.lsst.codes).

## Installation

This package is part of the [LSST Science Pipelines](https://pipelines.lsst.io).
You can learn how to install the Pipelines at https://pipelines.lsst.io/install.

## Installation for developers

To develop this package, you can clone `validate_base` and install it into your *existing* Pipelines stack:

```
git clone https://github.com/lsst/validate_base
cd validate_base
eups declare -r . -t $USER validate_base git
setup -r . -t $USER
scons
```

## Getting help and reporting bugs

If you're not part of the LSST Project, please post your question or issue in [our support forum](https://community.lsst.org/c/support).
It's easy to create a Community forum account.

*We don't use GitHub Issues.*

If you're part of the LSST Project, please create a [JIRA ticket](https://jira.lsstcorp.org/).
Use the `QA` component.

## Contributing code

Follow [LSST Data Management's workflow](https://developer.lsst.io/processes/workflow.html) for code contributions.

## License

This product includes software developed by the [LSST Project](http://www.lsst.org/).
See the [COPYRIGHT](./COPYRIGHT) file.

This product's source code is licensed under the terms of GPLv3 (see [LICENSE](./LICENSE)), and all documentation content is licensed under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.
