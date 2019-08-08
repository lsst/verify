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
"""SQUASH (https://squash.lsst.codes) client.

Data objects, particularly Job, Metric, and Specification, use this client to
upload and retrieve data from the SQUASH verification database.

SQUASH will likely be replaced by a database served behind Data Management's
webserv API. This client is considered a shim during construction.
"""

__all__ = ['get', 'post', 'get_endpoint_url', 'reset_endpoint_cache',
           'get_default_timeout', 'get_default_api_version',
           'make_accept_header']


import requests

import lsst.log

# Version of the SQUASH API this client is compatible with
_API_VERSION = '1.0'

# Default HTTP timeout (seconds) for all SQUASH client requests.
_TIMEOUT = 900.0

# URLs for SQUASH endpoints, cached by `get_endpoint_url()`.
_ENDPOINT_URLS = None


def get_endpoint_url(api_url, api_endpoint, **kwargs):
    """Lookup SQUASH endpoint URL.

    Parameters
    ----------
    api_url : `str`
        Root URL of the SQUASH API. For example,
        ``'https://squash.lsst.codes/dashboard/api/'``.
    api_endpoint : `str`
        Name of the SQUASH API endpoint. For example, ``'job'``.
    **kwargs : optional
        Additional keyword arguments passed to `get`.

    Returns
    -------
    endpoint_url : `str`
        Full SQUASH endpoint URL.

    Notes
    -----
    Endpoints are discovered from the SQUASH API itself. The SQUASH API is
    queried on the first call to `get_endpoint_url`. Subsequent calls use
    cached results for all endpoints. This cache can be reset with the
    `reset_endpoint_cache` function.
    """
    global _ENDPOINT_URLS

    if _ENDPOINT_URLS is None:
        r = get(api_url, **kwargs)
        _ENDPOINT_URLS = r.json()

    return _ENDPOINT_URLS[api_endpoint]


def reset_endpoint_cache():
    """Reset the cache used by `get_endpoint_url`.
    """
    global _ENDPOINT_URLS
    _ENDPOINT_URLS = None


def get_default_timeout():
    """Get the default HTTP client timeout setting.

    Returns
    -------
    timeout : `float`
        Default timeout setting, in seconds.
    """
    global _TIMEOUT
    return _TIMEOUT


def get_default_api_version():
    """Get the default SQUASH API versioned used by the lsst.verify.squash
    client functions.

    Returns
    -------
    version : `str`
        API version. For example, ``'1.0'``.
    """
    global _API_VERSION
    return _API_VERSION


def make_accept_header(version=None):
    """Make the ``Accept`` HTTP header for versioned SQUASH API requests.

    Parameters
    ----------
    version : `str`, optional
        Semantic API version, such as ``'1.0'``. By default, the API version
        this client is designed for is used (`get_default_api_version`).

    Returns
    -------
    accept_header : `str`
        The ``Accept`` header value.

    Examples
    --------
    >>> make_accept_header()
    'application/json; version=1.0'
    """
    if version is None:
        version = get_default_api_version()
    template = 'application/json; version={0}'
    return template.format(version)


def get_access_token(api_url, api_user, api_password,
                     api_auth_endpoint='auth'):
    """Get access token from the SQUASH API assuming the API user exists.

    Parameters
    ----------
    api_url : `str`
        Root URL of the SQUASH API. For example,
        ```https://squash-restful-api.lsst.codes```.
    api_user : `str`
        API username.
    api_password : `str`
        API password.
    api_auth_endpoint : `str`
        API authorization endpoint.

    Returns
    -------
    access_token: `str`
       The access token from the SQUASH API authorization endpoint.
    """
    json_doc = {'username': api_user, 'password': api_password}

    r = post(api_url, api_auth_endpoint, json_doc)

    json_r = r.json()

    return json_r['access_token']


def make_authorization_header(access_token):
    """Make an ``Authorization`` HTTP header using a SQUASH access token.

    Parameters
    ----------
    access_token : `str`
        Access token returned by `get_access_token`.

    Returns
    -------
    authorization_header : `str`
        The Authorization header value.
    """
    authorization_header = 'JWT {0}'
    return authorization_header.format(access_token)


def post(api_url, api_endpoint, json_doc=None,
         timeout=None, version=None, access_token=None):
    """POST a JSON document to SQUASH.

    Parameters
    ----------
    api_url : `str`
        Root URL of the SQUASH API. For example,
        ``'https://squash.lsst.codes/api'``.
    api_endpoint : `str`
        Name of the API endpoint to post to.
    json_doc : `dict`
        A JSON-serializable object.
    timeout : `float`, optional
        Request timeout. The value of `get_default_timeout` is used by default.
    version : `str`, optional
        API version. The value of `get_default_api_version` is used by default.
    access_token : `str`, optional
        Access token (see `get_access_token`). Not required when a POST is done
        to the API authorization endpoint.

    Raises
    ------
    requests.exceptions.RequestException
       Raised if the HTTP request fails.

    Returns
    -------
    response : `requests.Response`
        Response object. Obtain JSON content with ``response.json()``.
    """
    log = lsst.log.Log.getLogger('verify.squash.post')

    api_endpoint_url = get_endpoint_url(api_url, api_endpoint)

    headers = {
        'Accept': make_accept_header(version)
    }

    if access_token:
        headers['Authorization'] = make_authorization_header(access_token)

    try:
        # Disable redirect following for POST as requests will turn a POST into
        # a GET when following a redirect. http://ls.st/pbx
        r = requests.post(api_endpoint_url,
                          json=json_doc,
                          allow_redirects=False,
                          headers=headers,
                          timeout=timeout or get_default_timeout())
        log.info('POST {0} status: {1}'.format(api_endpoint_url,
                                               r.status_code))
        r.raise_for_status()

        # be pedantic about return status. requests#status_code will not error
        # on 3xx codes
        if r.status_code != 200 and r.status_code != 201 \
                and r.status_code != 202:
            message = 'Expected status = 200(OK), 201(Created) or 202' \
                      '(Accepted). Got status={0}. {1}'.format(r.status_code,
                                                               r.reason)
            raise requests.exceptions.RequestException(message)
    except requests.exceptions.RequestException as e:
        log.error(str(e))
        raise e

    return r


def get(api_url, api_endpoint=None,
        api_user=None, api_password=None, timeout=None, version=None):
    """GET request to the SQUASH API.

    Parameters
    ----------
    api_url : `str`
        Root URL of the SQUASH API. For example,
        ``'https://squash.lsst.codes/api'``.
    api_endpoint : `str`, optional
        Name of the API endpoint to post to. The ``api_url`` is requested if
        unset.
    api_user : `str`, optional
        API username.
    api_password : `str`, optional
        API password.
    timeout : `float`, optional
        Request timeout. The value of `get_default_timeout` is used by default.
    version : `str`, optional
        API version. The value of `get_default_api_version` is used by default.

    Raises
    ------
    requests.exceptions.RequestException
       Raised if the HTTP request fails.

    Returns
    -------
    response : `requests.Response`
        Response object. Obtain JSON content with ``response.json()``.
    """
    log = lsst.log.Log.getLogger('verify.squash.get')

    if api_user is not None and api_password is not None:
        auth = (api_user, api_password)
    else:
        auth = None

    if api_endpoint is not None:
        api_endpoint_url = get_endpoint_url(api_url, api_endpoint)
    else:
        api_endpoint_url = api_url

    headers = {
        'Accept': make_accept_header(version)
    }

    try:
        r = requests.get(api_endpoint_url,
                         auth=auth,
                         headers=headers,
                         timeout=timeout or get_default_timeout())
        log.info('GET {0} status: {1}'.format(api_endpoint_url,
                                              r.status_code))
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        log.error(str(e))
        raise e

    return r
