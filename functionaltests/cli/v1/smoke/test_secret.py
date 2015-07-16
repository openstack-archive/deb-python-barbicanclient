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

from functionaltests.cli.base import CmdLineTestCase
from functionaltests.cli.v1.behaviors.secret_behaviors import SecretBehaviors
from testtools import testcase


class SecretTestCase(CmdLineTestCase):

    def setUp(self):
        super(SecretTestCase, self).setUp()
        self.secret_behaviors = SecretBehaviors()
        self.expected_payload = "Top secret payload for secret smoke tests"

    def tearDown(self):
        super(SecretTestCase, self).tearDown()
        self.secret_behaviors.delete_all_created_secrets()

    @testcase.attr('positive')
    def test_secret_store(self):
        secret_href = self.secret_behaviors.store_secret()
        self.assertIsNotNone(secret_href)

        secret = self.secret_behaviors.get_secret(secret_href)
        self.assertEqual(secret_href, secret['Secret href'])

    @testcase.attr('positive')
    def test_secret_list(self):
        secrets_to_create = 10
        for _ in range(secrets_to_create):
            self.secret_behaviors.store_secret()
        secret_list = self.secret_behaviors.list_secrets()
        self.assertGreaterEqual(len(secret_list), secrets_to_create)

    @testcase.attr('positive')
    def test_secret_delete(self):
        secret_href = self.secret_behaviors.store_secret()
        self.secret_behaviors.delete_secret(secret_href)

        secret = self.secret_behaviors.get_secret(secret_href)
        self.assertEqual(0, len(secret))

    @testcase.attr('positive')
    def test_secret_get(self):
        secret_href = self.secret_behaviors.store_secret()
        secret = self.secret_behaviors.get_secret(secret_href)
        self.assertIsNotNone(secret)

    @testcase.attr('positive')
    def test_secret_get_payload(self):
        secret_href = self.secret_behaviors.store_secret(
            payload=self.expected_payload)
        payload = self.secret_behaviors.get_secret_payload(secret_href)
        self.assertEqual(payload, self.expected_payload)

    @testcase.attr('positive')
    def test_secret_get_raw_payload(self):
        secret_href = self.secret_behaviors.store_secret(
            payload=self.expected_payload)
        payload = self.secret_behaviors.get_secret_payload(secret_href,
                                                           raw=True)
        self.assertEqual(payload, self.expected_payload)
