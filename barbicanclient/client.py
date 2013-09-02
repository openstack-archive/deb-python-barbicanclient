import json
import os
import urlparse

import requests

from barbicanclient import secrets
from barbicanclient.secrets import Secret
from barbicanclient.orders import Order
from barbicanclient.common import auth
from barbicanclient.openstack.common import log
from barbicanclient.common.exceptions import ClientException
from barbicanclient.openstack.common.gettextutils import _
from urlparse import urljoin


LOG = log.getLogger(__name__)
log.setup('barbicanclient')


class Client(object):
    SECRETS_PATH = 'secrets'
    ORDERS_PATH = 'orders'

    def __init__(self, auth_plugin=None, endpoint=None, tenant_id=None,
                 **kwargs):
        """
        Authenticate and connect to the service endpoint, which can be
        received through authentication.

        Environment variables will be used by default when their corresponding
        arguments are not passed in.

        :param auth_plugin: Authentication backend plugin
            defaults to None
        :param endpoint: Barbican endpoint url

        :param key: The API key or password to auth with
        :keyword param endpoint: The barbican endpoint to connect to
            default: env('BARBICAN_ENDPOINT')
        """

        LOG.debug(_("Creating Client object"))

        self._session = requests.Session()
        self.auth_plugin = auth_plugin

        if self.auth_plugin is not None:
            self._barbican_url = self.auth_plugin.barbican_url
            self._tenant_id = self.auth_plugin.tenant_id
            self._session.headers.update(
                {'X-Auth-Token': self.auth_plugin.auth_token}
            )
        else:
            if endpoint is None:
                raise ValueError('Barbican endpoint url must be provided, or '
                                 'must be available from auth_plugin')
            if tenant_id is None:
                raise ValueError('Tenant ID must be provided, or must be available'
                                 ' from auth_plugin')
            if endpoint.endswith('/'):
                self._barbican_url = endpoint[:-1]
            else:
                self._barbican_url = endpoint
            self._tenant_id = tenant_id

        self.base_url = '{0}/{1}'.format(self._barbican_url, self._tenant_id)
        self.secrets = secrets.SecretManager(self)

        # self.env = kwargs.get('fake_env') or env

        # #TODO(dmend): remove these
        # self._auth_endpoint = kwargs.get('auth_endpoint') or self.env('OS_AUTH_URL')
        # self._user = kwargs.get('user') or self.env('OS_USERNAME')
        # self._tenant = kwargs.get('tenant') or self.env('OS_TENANT_NAME')
        # self._key = kwargs.get('key')

        # if not all([self._auth_endpoint, self._user, self._key, self._tenant]):
        #     raise ClientException("The authorization endpoint, username, key,"
        #                           " and tenant name should either be passed i"
        #                           "n or defined as environment variables.")
        # self.authenticate = kwargs.get('authenticate') or auth.authenticate
        # self.request = kwargs.get('request') or requests.request
        # self._endpoint = (kwargs.get('endpoint') or
        #                   self.env('BARBICAN_ENDPOINT'))
        # self._cacert = kwargs.get('cacert')
        # self.connect(token=(kwargs.get('token') or self.env('AUTH_TOKEN')))

    @property
    def _conn(self):
        """Property to enable decorators to work properly"""
        return self

    @property
    def auth_endpoint(self):
        """The fully-qualified URI of the auth endpoint"""
        return self._auth_endpoint

    @property
    def endpoint(self):
        """The fully-qualified URI of the endpoint"""
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    def connect(self, token=None):
        """
        Establishes a connection. If token is not None or empty, it will be
        used for this connection, and authentication will not take place.

        :param token: An authentication token
        """

        LOG.debug(_("Establishing connection"))

        self._session = requests.Session()

        # headers = {"Client-Id": self._client_id}
        # self._session.headers.update(headers)
        self._session.verify = True

        if token:
            self.auth_token = token
        else:
            LOG.debug(_("Authenticating token"))
            endpoint, self.auth_token = self.authenticate(
                self._auth_endpoint,
                self._user,
                self._key,
                self._tenant,
                service_type='key-store',
                endpoint=self._endpoint,
                cacert=self._cacert
            )
            if self.endpoint is None:
                self.endpoint = endpoint

    @property
    def auth_token(self):
        try:
            return self._session.headers['X-Auth-Token']
        except KeyError:
            return None

    @auth_token.setter
    def auth_token(self, value):
        self._token = value
        self._session.headers['X-Auth-Token'] = value

    def list_orders(self, limit=10, offset=0):
        """
        Returns a tuple containing three items: a list of orders pertaining
        to the given offset and limit, a reference to the previous set of
        orders, and a reference to the next set of orders. Either of the
        references may be None.

        :param limit: The limit to the number of orders to list
        :param offset: The offset from the beginning to start listing
        """
        LOG.debug(_("Listing orders - offset: {0}, limit: {1}").format(offset,
                                                                       limit))
        href = "{0}/{1}?limit={2}&offset={3}".format(self._tenant,
                                                     self.ORDERS_PATH,
                                                     limit, offset)
        return self.list_orders_by_href(href)

    def list_orders_by_href(self, href):
        """
        Returns a tuple containing three items: a list of orders pertaining
        to the offset and limit within href, a reference to the previous set
        of orders, and a reference to the next set of orders. Either of the
        references may be None.

        :param href: The full orders URI
        """
        LOG.debug(_("Listing orders by href"))
        LOG.debug("href: {0}".format(href))
        if href is None:
            return [], None, None

        hdrs, body = self._perform_http(href=href, method='GET')
        LOG.debug(_("Response - headers: {0}\nbody: {1}").format(hdrs, body))

        orders_dict = body['orders']
        orders = [Order(self._conn, o) for o in orders_dict]

        prev_ref = body.get('previous')

        next_ref = body.get('next')

        return orders, prev_ref, next_ref

    def create_order(self,
                     name=None,
                     payload_content_type='application/octet-stream',
                     algorithm='aes',
                     bit_length=256,
                     cypher_type='cbc',
                     expiration=None):
        """
        Creates and returns an Order object with all of its metadata filled in.

        :param name: A friendly name for the secret
        :param algorithm: The algorithm the secret is used with
        :param bit_length: The bit length of the secret
        :param cypher_type: The cypher type (e.g. block cipher mode)
        :param expiration: The expiration time of the secret in ISO 8601 format
        """
        LOG.debug(_("Creating order"))
        href = "{0}/{1}".format(self._tenant, self.ORDERS_PATH)
        LOG.debug("href: {0}".format(href))
        order_dict = {'secret': {}}
        order_dict['secret']['name'] = name
        order_dict['secret'][
            'payload_content_type'] = payload_content_type
        order_dict['secret']['algorithm'] = algorithm
        order_dict['secret']['bit_length'] = bit_length
        order_dict['secret']['cypher_type'] = cypher_type
        order_dict['secret']['expiration'] = expiration
        self._remove_empty_keys(order_dict['secret'])
        LOG.debug(_("Request body: {0}").format(order_dict['secret']))
        hdrs, body = self._perform_http(href=href,
                                        method='POST',
                                        request_body=json.dumps(order_dict))

        LOG.debug(_("Response - headers: {0}\nbody: {1}").format(hdrs, body))

        return self.get_order(body['order_ref'])

    def delete_order_by_id(self, order_id):
        """
        Deletes an order

        :param order_id: The UUID of the order
        """
        LOG.info(_("Deleting order - Order ID: {0}").format(order_id))
        href = "{0}/{1}/{2}".format(self._tenant, self.ORDERS_PATH, order_id)
        return self.delete_order(href)

    def delete_order(self, href):
        """
        Deletes an order

        :param href: The full URI of the order
        """
        hdrs, body = self._perform_http(href=href, method='DELETE')
        LOG.debug(_("Response - headers: {0}\nbody: {1}").format(hdrs, body))

    def get_order_by_id(self, order_id):
        """
        Returns an Order object

        :param order_id: The UUID of the order
        """
        LOG.debug(_("Getting order - Order ID: {0}").format(order_id))
        href = "{0}/{1}/{2}".format(self._tenant, self.ORDERS_PATH, order_id)
        return self.get_order(href)

    def get_order(self, href):
        """
        Returns an Order object

        :param href: The full URI of the order
        """
        hdrs, body = self._perform_http(href=href, method='GET')
        LOG.debug(_("Response - headers: {0}\nbody: {1}").format(hdrs, body))
        return Order(self._conn, body)

    def _perform_http(self, method, href, request_body='', headers={},
                      parse_json=True):
        """
        Perform an HTTP operation, checking for appropriate
        errors, etc. and returns the response

        Returns the headers and body as a tuple.

        :param method: The http method to use (GET, PUT, etc)
        :param body: The optional body to submit
        :param headers: Any additional headers to submit
        :param parse_json: Whether the response body should be parsed as json
        """
        if not isinstance(request_body, str):
            request_body = json.dumps(request_body)

        if not self.endpoint.endswith('/'):
            self.endpoint += '/'

        url = urljoin(self.endpoint, href)

        headers['X-Auth-Token'] = self.auth_token

        response = self.request(method=method, url=url, data=request_body,
                                headers=headers)
        # Check if the status code is 2xx class
        if not response.ok:
            LOG.error('Bad response: {0}'.format(response.status_code))
            raise ClientException(href=href, method=method,
                                  http_status=response.status_code,
                                  http_response_content=response.content)

        if response.content and parse_json is True:
            resp_body = json.loads(response.content)
        elif response.content and parse_json is False:
            resp_body = response.content
        else:
            resp_body = ''

        return response.headers, resp_body

    def _request(self, url, method, headers):
        resp = self._session.request()

    def get(self, path, params=None):
        url = '{0}/{1}/'.format(self.base_url, path)
        headers = {'Accept': 'application/json'}
        resp = self._session.get(url, params=params, headers=headers)
        self._check_status_code(resp)
        return resp.json()

    def get_raw(self, path, headers):
        url = '{0}/{1}/'.format(self.base_url, path)
        resp = self._session.get(url, headers=headers)
        self._check_status_code(resp)
        return resp.content

    def post(self, path, data):
        url = '{0}/{1}/'.format(self.base_url, path)
        headers = {'content-type': 'application/json'}
        resp = self._session.post(url, data=json.dumps(data), headers=headers)
        self._check_status_code(resp)
        return resp.json()

    def delete(self, path):
        url = '{0}/{1}/'.format(self.base_url, path)
        resp = self._session.delete(url)
        self._check_status_code(resp)

    #TODO(dmend): beef this up
    def _check_status_code(self, resp):
        status = resp.status_code
        print('status {0}'.format(status))


def env(*vars, **kwargs):
    """Search for the first defined of possibly many env vars

    Returns the first environment variable defined in vars, or
    returns the default defined in kwargs.

    Source: Keystone's shell.py
    """
    for v in vars:
        value = os.environ.get(v, None)
        if value:
            return value
    return kwargs.get('default', '')
