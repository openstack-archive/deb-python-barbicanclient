# Copyright (c) 2015 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from testtools import testcase

from functionaltests import utils
from functionaltests.client import base
from functionaltests.common import cleanup


order_create_key_data = {
    "name": "barbican functional test secret name",
    "algorithm": "aes",
    "bit_length": 256,
    "mode": "cbc",
    "payload_content_type": "application/octet-stream",
}

# Any field with None will be created in the model with None as the value
# but will be omitted in the final request (via the requests package)
# to the server.
#
# Given that fact, order_create_nones_data is effectively an empty json request
# to the server.
order_create_nones_data = {
    'type': None,
    "meta": {
        "name": None,
        "algorithm": None,
        "bit_length": None,
        "mode": None,
        "payload_content_type": None,
    }
}


@utils.parameterized_test_case
class OrdersTestCase(base.TestCase):

    def setUp(self):
        super(OrdersTestCase, self).setUp()
        self.cleanup = cleanup.CleanUp(self.barbicanclient)

    def tearDown(self):
        self.cleanup.delete_all_entities()
        super(OrdersTestCase, self).tearDown()

    @testcase.attr('positive')
    def test_create_order_defaults(self):
        """Covers simple order creation."""
        order = self.barbicanclient.orders.create_key(
            **order_create_key_data)
        order_ref = self.cleanup.add_entity(order)

        self.assertIsNotNone(order_ref)

    @testcase.attr('positive')
    def test_get_order_defaults_metadata(self):
        """Covers order metadata.

        Assumes that the order status will be active or pending.
        """

        # first create an order
        order = self.barbicanclient.orders.create_key(
            **order_create_key_data)
        order_ref = self.cleanup.add_entity(order)

        # verify that the order was created successfully
        self.assertIsNotNone(order_ref)

        # given the order href, retrieve the order
        order_resp = self.barbicanclient.orders.get(order_ref)

        # verify that the get was successful
        self.assertTrue(order_resp.status == "ACTIVE" or
                        order_resp.status == "PENDING")

        # verify the metadata
        self.assertEqual(order_resp.name,
                         order.name)
        self.assertEqual(order_resp.mode,
                         order.mode)
        self.assertEqual(order_resp.algorithm,
                         order.algorithm)
        self.assertEqual(order_resp.bit_length,
                         order.bit_length)

    @testcase.attr('positive')
    def test_get_order_defaults(self):
        """Covers getting an order.

        Assumes that the order status will be active or pending.
        """

        # create an order
        order = self.barbicanclient.orders.create_key(
            **order_create_key_data)
        order_ref = self.cleanup.add_entity(order)
        self.assertIsNotNone(order_ref)

        # get the order
        order_resp = self.barbicanclient.orders.get(order_ref)

        # verify the order
        self.assertIsNotNone(order_resp.order_ref)
        self.assertEqual(order_resp._type, 'key')
        self.assertTrue(order_resp.status == "ACTIVE" or
                        order_resp.status == "PENDING")

        if order_resp.status == "ACTIVE":
            self.assertIsNotNone(order_resp.secret_ref)

    @testcase.attr('positive')
    def test_delete_order_defaults(self):
        """Covers simple order deletion."""

        # create an order
        order = self.barbicanclient.orders.create_key(
            **order_create_key_data)
        order_ref = order.submit()
        secret_ref = self.barbicanclient.orders.get(order_ref).secret_ref

        # delete the order
        delete_resp = self.barbicanclient.orders.delete(order_ref)
        self.assertIsNone(delete_resp)

        # delete the secret
        self.barbicanclient.secrets.delete(secret_ref)

    @testcase.attr('positive')
    def test_get_orders_defaults(self):
        """Covers getting a list of orders."""
        limit = 7
        offset = 0
        total = 10

        # create the orders
        for i in range(0, total + 1):
            order = self.barbicanclient.orders.create_key(
                **order_create_key_data)
            order_ref = self.cleanup.add_entity(order)
            self.assertIsNotNone(order_ref)

        # get a list of orders
        orders_list = self.barbicanclient.orders.list(limit=limit,
                                                      offset=offset)

        # verify that the get for the list was successful
        self.assertEqual(len(orders_list), limit)
