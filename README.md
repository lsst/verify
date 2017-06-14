# lsst.verify

**LSST Science Pipelines Verification Framework.**

Packages can use `lsst.verify` to report metric measurements to LSST Data Management's [SQUASH](https://squash.lsst.codes) dashboard.
The [verify_metrics](https://github.com/lsst/verify_metrics) package supplies metric and specification definitions.

For background on the Verification Framework, see the [SQR-017](https://sqr-017.lsst.io) (design) and [SQR-019](https://sqr-019.lsst.io) (API demo) technotes.

## Installation

This package is part of the [LSST Science Pipelines](https://pipelines.lsst.io) and included in the `lsst_distrib` distribution.

You can learn how to install the Pipelines at https://pipelines.lsst.io/install.

## Installation for developers

To develop this package, you can clone `verify` and install it into your *existing* Pipelines stack:

```
git clone https://github.com/lsst/verify
cd verify
eups declare -r . -t $USER verify git
setup -r . -t $USER
scons
```

## Getting help and reporting bugs

If you're not part of the LSST Project, please post your question or issue in [our support forum](https://community.lsst.org/c/support).
It's easy to create a Community forum account.

*We don't use GitHub Issues.*

If you're part of the LSST Project, please create a [JIRA ticket](https://jira.lsstcorp.org/).
Use the [Verification component](https://jira.lsstcorp.org/browse/DM/component/14170) and [verify label](https://jira.lsstcorp.org/issues/?jql=labels%20%3D%20verify).

## Contributing code

Follow [LSST Data Management's workflow](https://developer.lsst.io/processes/workflow.html) for code contributions.

## License

This product includes software developed by the [LSST Project](http://www.lsst.org/).
See the [COPYRIGHT](./COPYRIGHT) file.

This product's source code is licensed under the terms of GPLv3 (see [LICENSE](./LICENSE)), and all documentation content is licensed under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.
