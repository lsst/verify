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

import json
import unittest

import requests
try:
    # responses is not a formal LSST Stack dependency (yet), so we'll skip any
    # tests that require it in environments that don't have it.
    import responses
except ImportError:
    responses = None

from lsst.verify import squash


class GetDefaultTimeoutTestCase(unittest.TestCase):

    def test_get_default_timeout(self):
        self.assertEqual(
            squash.get_default_timeout(),
            squash._TIMEOUT
        )


class GetDefaultApiVersionTestCase(unittest.TestCase):

    def test_get_default_api_version(self):
        self.assertEqual(
            squash.get_default_api_version(),
            squash._API_VERSION
        )


class MakeAcceptHeaderTestCase(unittest.TestCase):

    def test_make_accept_header(self):
        self.assertEqual(
            squash.make_accept_header(),
            'application/json; version=' + squash.get_default_api_version()
        )

        self.assertEqual(
            squash.make_accept_header(1.1),
            'application/json; version=1.1'
        )


class GetEndpointUrlTestCase(unittest.TestCase):

    def setUp(self):
        self.api_url = 'https://example.com/api/'
        self.endpoints = {
            'jobs': 'https://example.com/api/jobs/'
        }
        squash.reset_endpoint_cache()

    def tearDown(self):
        squash.reset_endpoint_cache()

    @unittest.skipIf(responses is None,
                     'Requires `responses` PyPI package')
    def test_jobs(self):
        with responses.RequestsMock() as reqmock:
            reqmock.add(responses.GET,
                        self.api_url,
                        json=self.endpoints,
                        status=200,
                        content_type='application/json')
            jobs_url = squash.get_endpoint_url(self.api_url, 'jobs')

            self.assertEqual(jobs_url, self.endpoints['jobs'])

            # call again, shouldn't register a new request
            jobs_url = squash.get_endpoint_url(self.api_url, 'jobs')

            self.assertEqual(jobs_url, self.endpoints['jobs'])
            self.assertEqual(len(reqmock.calls), 1)


class GetTestCase(unittest.TestCase):

    def setUp(self):
        self.api_url = 'https://example.com/api/'
        # pre-set the _ENDPOINT_URLS to use the cache, not http get
        squash._ENDPOINT_URLS = {
            'jobs': self.api_url + 'jobs'
        }

    def tearDown(self):
        squash.reset_endpoint_cache()

    @unittest.skipIf(responses is None,
                     'Requires `responses` PyPI package')
    def test_get(self):
        with responses.RequestsMock() as reqmock:
            reqmock.add(responses.GET,
                        squash._ENDPOINT_URLS['jobs'],
                        json={},
                        status=200,
                        content_type='application/json')

            r = squash.get(self.api_url, api_endpoint='jobs')

            self.assertIsInstance(r, requests.Response)
            self.assertEqual(len(reqmock.calls), 1)
            self.assertEqual(
                reqmock.calls[0].request.url,
                squash._ENDPOINT_URLS['jobs'],
            )
            self.assertEqual(
                reqmock.calls[0].request.headers['Accept'],
                'application/json; version=' + squash._API_VERSION
            )

    @unittest.skipIf(responses is None,
                     'Requires `responses` PyPI package')
    def test_versioned_get(self):
        with responses.RequestsMock() as reqmock:
            reqmock.add(responses.GET,
                        squash._ENDPOINT_URLS['jobs'],
                        json={},
                        status=200,
                        content_type='application/json')

            squash.get(self.api_url, api_endpoint='jobs', version='1.2')

            self.assertEqual(
                reqmock.calls[0].request.headers['Accept'],
                'application/json; version=1.2'
            )

    @unittest.skipIf(responses is None,
                     'Requires `responses` PyPI package')
    def test_raises(self):
        with responses.RequestsMock() as reqmock:
            reqmock.add(responses.GET,
                        squash._ENDPOINT_URLS['jobs'],
                        json={},
                        status=404,
                        content_type='application/json')

            with self.assertRaises(requests.exceptions.RequestException):
                squash.get(self.api_url, api_endpoint='jobs', version='1.2')


class PostTestCase(unittest.TestCase):

    def setUp(self):
        self.api_url = 'https://example.com/api/'
        # pre-set the _ENDPOINT_URLS to use the cache, not http get
        squash._ENDPOINT_URLS = {
            'jobs': self.api_url + 'jobs'
        }

    def tearDown(self):
        squash.reset_endpoint_cache()

    @unittest.skipIf(responses is None,
                     'Requires `responses` PyPI package')
    def test_json_post(self):
        with responses.RequestsMock() as reqmock:
            reqmock.add(responses.POST,
                        squash._ENDPOINT_URLS['jobs'],
                        json={},
                        status=201,
                        content_type='application/json')

            r = squash.post(self.api_url, api_endpoint='jobs',
                            json_doc={'key': 'value'},
                            api_user='foo', api_password='bar')

            self.assertIsInstance(r, requests.Response)
            self.assertEqual(len(reqmock.calls), 1)
            self.assertEqual(
                reqmock.calls[0].request.url,
                squash._ENDPOINT_URLS['jobs'],
            )
            self.assertEqual(
                reqmock.calls[0].request.headers['Accept'],
                'application/json; version=' + squash._API_VERSION
            )
            self.assertEqual(
                json.loads(reqmock.calls[0].request.body),
                {'key': 'value'}
            )

    @unittest.skipIf(responses is None,
                     'Requires `responses` PyPI package')
    def test_raises(self):
        with responses.RequestsMock() as reqmock:
            reqmock.add(responses.POST,
                        squash._ENDPOINT_URLS['jobs'],
                        json={},
                        status=503,
                        content_type='application/json')

            with self.assertRaises(requests.exceptions.RequestException):
                squash.post(self.api_url, api_endpoint='jobs',
                            json_doc={},
                            api_user='foo', api_password='bar')


if __name__ == "__main__":
    unittest.main()
