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
"""Upload LSST Science Pipelines Verification `~lsst.verify.Job` datasets to
the SQUASH dashboard.

Job JSON files can be created by `lsst.verify.Job.write` or
`lsst.verify.output_quantities`. A `~lsst.verify.Job` dataset consists of
metric measurements, associated blobs, and pipeline execution metadata.
Individual LSST Science Pipelines tasks typically write separate JSON datasets.
This command can collect and combine multiple Job JSON datasets into a single
Job upload.

**Configuration**

dispatch_verify.py is configurable from both the command line and environment
variables. See the argument documenation for environment variable equivalents.
Command line settings override environment variable configuration.

**Metadata and environment**

dispatch_verify.py can enrich Verification Job metadata with information
from the environment. Currently dispatch_verify.py supports the Jenkins CI
and the LSST Data Facility (LDF) execution environments.

In the Jenkins CI execution environment (``--env=jenkins``) the
following environment variables are consumed:

- ``BUILD_ID``: ID in the CI system
- ``BUILD_URL``: CI page with information about the build
- ``PRODUCT``: the name of the product built, e.g. 'validate_drp'
- ``dataset``: the name of the dataset processed, e.g. 'validation_data_cfht'
- ``label``: the name of the platform where it runs

If ``--lsstsw`` is used, additional Git branch information is included with
Science Pipelines package metadata.

In the LSST Data Facility execution environment (``--env=ldf``) the following
environment variables are consumed:

- ``DATASET``: the name of the dataset processed, e.g 'HSC RC2'
- ``DATASET_REPO_URL``: a reference URL with information about the dataset
- ``RUN_ID``: ID of the run in the LDF environment
- ``RUN_ID_URL``: a reference URL with information about the run
- ``VERSION_TAG``: the version tag of the LSST software used, e.g. 'w_2018_18'

Note: currently it is not possible to gather Science Pipelines package metadata
in the LDF environment, thus if ``--env=ldf`` is used ``--ignore-lsstsw`` is
aslo used by default in this environment.
"""
# For determining what is documented in Sphinx
__all__ = ['parse_args', 'main', 'insert_lsstsw_metadata',
           'insert_extra_package_metadata', 'insert_env_metadata',
           'Configuration']

import argparse
import os
import json

try:
    import git
except ImportError:
    # GitPython is not a standard Stack package; skip gracefully if unavailable
    git = None

import lsst.log
from lsst.verify import Job
from lsst.verify.metadata.lsstsw import LsstswRepos
from lsst.verify.metadata.eupsmanifest import Manifest
from lsst.verify.metadata.jenkinsci import get_jenkins_env
from lsst.verify.metadata.ldf import get_ldf_env


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='More information is available at https://pipelines.lsst.io.')

    parser.add_argument(
        'json_paths',
        nargs='+',
        metavar='json',
        help='Verificaton job JSON file, or files. When multiple JSON '
             'files are present, their measurements, blobs, and metadata '
             'are merged.')
    parser.add_argument(
        '--test',
        default=False,
        action='store_true',
        help='Run this command without uploading to the SQUASH service. '
             'The JSON payload is printed to standard out.')
    parser.add_argument(
        '--write',
        metavar='PATH',
        dest='output_filepath',
        help='Write the merged and enriched Job JSON dataset to the given '
             'path.')
    parser.add_argument(
        '--show',
        dest='show_json',
        action='store_true',
        default=False,
        help='Print the assembled Job JSON to standard output.')
    parser.add_argument(
        '--ignore-blobs',
        dest='ignore_blobs',
        action='store_true',
        default=False,
        help='Ignore data blobs even if they are available in the verification'
             'job.')

    env_group = parser.add_argument_group('Environment arguments')
    env_group.add_argument(
        '--env',
        dest='env_name',
        choices=Configuration.allowed_env,
        help='Name of the environment where the verification job is being '
             'run. In some environments display_verify.py will gather '
             'additional metadata automatically. '
             '**jenkins**: for the Jenkins CI (https://ci.lsst.codes)'
             'environment.'
             '**ldf**: for the LSST Data Facility environment. '
             'Equivalent to the $VERIFY_ENV environment variable.')
    env_group.add_argument(
        '--lsstsw',
        dest='lsstsw',
        metavar='PATH',
        help='lsstsw directory path. If available, Stack package versions are '
             'read from lsstsw. Equivalent to the $LSSTSW environment '
             'variable. Disabled with --ignore-lsstsw.')
    env_group.add_argument(
        '--package-repos',
        dest='extra_package_paths',
        nargs='*',
        metavar='PATH',
        help='Paths to additional Stack package Git repositories. These '
             'packages are tracked in Job metadata, like lsstsw-based '
             'packages.')
    env_group.add_argument(
        '--ignore-lsstsw',
        dest='ignore_lsstsw',
        action='store_true',
        default=False,
        help='Ignore lsstsw metadata even if it is available (for example, '
             'the $LSSTSW variable is set).')

    api_group = parser.add_argument_group('SQUASH API arguments')
    api_group.add_argument(
        '--url',
        dest='api_url',
        metavar='URL',
        help='Root URL of the SQUASH API. Equivalent to the $SQUASH_URL '
             'environment variable.')
    api_group.add_argument(
        '--user',
        dest='api_user',
        metavar='USER',
        help='Username for SQUASH API. Equivalent to the $SQUASH_USER '
             'environment variable.')
    api_group.add_argument(
        '--password',
        dest='api_password',
        metavar='PASSWORD',
        help='Password for SQUASH API. Equivalent to the $SQUASH_PASSWORD '
             'environment variable.')
    return parser.parse_args()


def main():
    """Entrypoint for the ``dispatch_verify.py`` command line executable.
    """
    log = lsst.log.Log.getLogger('verify.bin.dispatchverify.main')

    args = parse_args()
    config = Configuration(args)
    log.debug(str(config))

    # Parse all Job JSON
    jobs = []
    for json_path in config.json_paths:
        log.info('Loading {0}'.format(json_path))
        with open(json_path) as fp:
            json_data = json.load(fp)
            # Ignore blobs from the verification jobs
            if config.ignore_blobs:
                log.info('Ignoring blobs from Job JSON {0}'.format(json_path))
                json_data = delete_blobs(json_data)
        job = Job.deserialize(**json_data)
        jobs.append(job)

    # Merge all Jobs into one
    job = jobs.pop(0)
    if len(jobs) > 0:
        log.info('Merging verification Job JSON.')
    for other_job in jobs:
        job += other_job

    # Ensure all measurements have a metric so that units are normalized
    log.info('Refreshing metric definitions from verify_metrics')
    job.reload_metrics_package('verify_metrics')

    # Insert package metadata from lsstsw
    if not config.ignore_lsstsw:
        log.info('Inserting lsstsw package metadata from '
                 '{0}.'.format(config.lsstsw))
        job = insert_lsstsw_metadata(job, config)

    # Insert metadata from additional specified packages
    if config.extra_package_paths is not None:
        job = insert_extra_package_metadata(job, config)

    # Add environment variable metadata from the Jenkins CI environment
    if config.env_name == 'jenkins':
        log.info('Inserting Jenkins CI environment metadata.')
        jenkins_metadata = get_jenkins_env()
        job = insert_env_metadata(job, 'jenkins', jenkins_metadata)
    elif config.env_name == 'ldf':
        log.info('Inserting LSST Data Facility environment metadata.')
        ldf_metadata = get_ldf_env()
        job = insert_env_metadata(job, 'ldf', ldf_metadata)

    # Upload job
    if not config.test:
        log.info('Uploading Job JSON to {0}.'.format(config.api_url))
        job.dispatch(api_user=config.api_user,
                     api_password=config.api_password,
                     api_url=config.api_url)

    if config.show_json:
        print(json.dumps(job.json,
                         sort_keys=True, indent=4, separators=(',', ': ')))

    # Write a json file
    if config.output_filepath is not None:
        log.info('Writing Job JSON to {0}.'.format(config.output_filepath))
        job.write(config.output_filepath)


def delete_blobs(json_data):
    """Delete data blobs from the Job JSON
    """
    if 'blobs' in json_data:
        del json_data['blobs']
    return json_data


def insert_lsstsw_metadata(job, config):
    """Insert metadata for lsstsw-based packages into ``Job.meta['packages']``.
    """
    lsstsw_repos = LsstswRepos(config.lsstsw)

    with open(lsstsw_repos.manifest_path) as fp:
        manifest = Manifest(fp)

    packages = {}
    for package_name, manifest_item in manifest.items():
        package_doc = {
            'name': package_name,
            'git_branch': lsstsw_repos.get_package_branch(package_name),
            'git_url': lsstsw_repos.get_package_repo_url(package_name),
            'git_sha': manifest_item.git_sha,
            'eups_version': manifest_item.version
        }
        packages[package_name] = package_doc

    if 'packages' in job.meta:
        # Extend packages entry
        job.meta['packages'].update(packages)
    else:
        # Create new packages entry
        job.meta['packages'] = packages
    return job


def insert_extra_package_metadata(job, config):
    """Insert metadata for extra packages ('--package-repos') into
    ``Job.meta['packages']``.
    """
    log = lsst.log.Log.getLogger(
        'verify.bin.dispatchverify.insert_extra_package_metadata')

    if 'packages' not in job.meta:
        job.meta['packages'] = dict()

    for package_path in config.extra_package_paths:
        log.info('Inserting extra package metadata: {0}'.format(package_path))
        package_name = package_path.split(os.sep)[-1]

        package = {'name': package_name}

        if git is not None:
            git_repo = git.Repo(package_path)
            package['git_sha'] = git_repo.active_branch.commit.hexsha
            package['git_branch'] = git_repo.active_branch.name
            package['git_url'] = git_repo.remotes.origin.url

        if package_name in job.meta['packages']:
            # Update pre-existing package metadata
            job.meta['packages'][package_name].update(package)
        else:
            # Create new package metadata
            job.meta['packages'][package_name] = package

    return job


def insert_env_metadata(job, env_name, metadata):
    """Insert environment metadata into the Job.
    """
    metadata.update({'env_name': env_name})
    job.meta['env'] = metadata

    return job


class Configuration(object):
    """Configuration for dispatch_verify.py that reconciles command line and
    environment variable arguments.

    Configuration is validated for completeness and certain errors.

    Parameters
    ----------
    args : `argparse.Namespace`
        Parsed command line arguments, produced by `parse_args`.
    """

    allowed_env = ('jenkins', 'ldf')

    def __init__(self, args):
        self.json_paths = args.json_paths

        self.test = args.test

        self.output_filepath = args.output_filepath

        self.show_json = args.show_json

        self.env_name = args.env_name or os.getenv('VERIFY_ENV')
        if self.env_name is not None and self.env_name not in self.allowed_env:
            message = '$VERIFY_ENV not one of {0!s}'.format(self.allowed_env)
            raise RuntimeError(message)

        self.ignore_blobs = args.ignore_blobs

        self.ignore_lsstsw = args.ignore_lsstsw

        # Make sure --ignore-lsstw is used in the LDF environment
        if self.env_name == 'ldf':
            self.ignore_lsstsw = True

        self.lsstsw = args.lsstsw or os.getenv('LSSTSW')
        if self.lsstsw is not None:
            self.lsstsw = os.path.abspath(self.lsstsw)
        if not self.ignore_lsstsw and not self.lsstsw:
            message = 'lsstsw directory not found at {0}'.format(self.lsstsw)
            raise RuntimeError(message)

        if args.extra_package_paths is not None:
            self.extra_package_paths = [os.path.abspath(p)
                                        for p in args.extra_package_paths]
        else:
            self.extra_package_paths = []
        for path in self.extra_package_paths:
            if not os.path.isdir(path):
                message = 'Package directory not found: {0}'.format(path)
                raise RuntimeError(message)

        default_url = 'https://squash.lsst.codes/dashboard/api'
        self.api_url = args.api_url or os.getenv('SQUASH_URL', default_url)

        self.api_user = args.api_user or os.getenv('SQUASH_USER')
        if not self.test and self.api_user is None:
                message = '--user or $SQUASH_USER configuration required'
                raise RuntimeError(message)

        self.api_password = args.api_password or os.getenv('SQUASH_password')
        if not self.test and self.api_password is None:
                message = ('--password or $SQUASH_password configuration '
                           'required')
                raise RuntimeError(message)

    def __str__(self):
        configs = {
            'json_paths': self.json_paths,
            'test': self.test,
            'output_filepath': self.output_filepath,
            'show_json': self.show_json,
            'ignore_blobs': self.ignore_blobs,
            'env': self.env_name,
            'ignore_lsstsw': self.ignore_lsstsw,
            'lsstsw': self.lsstsw,
            'extra_package_paths': self.extra_package_paths,
            'api_url': self.api_url,
            'api_user': self.api_user,
        }
        if self.api_password is None:
            configs['api_password'] = None
        else:
            configs['api_password'] = '*' * len(self.api_password)

        return json.dumps(configs,
                          sort_keys=True, indent=4, separators=(',', ': '))
