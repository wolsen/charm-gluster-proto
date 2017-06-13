# Copyright 2017 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from ipaddress import ip_address

import mock
from result import Ok
import sys

from lib.gluster import lib

mock_apt = mock.MagicMock()
sys.modules['apt'] = mock_apt
mock_apt.apt_pkg = mock.MagicMock()


class TestResolveToIp(unittest.TestCase):
    @mock.patch("lib.gluster.lib.run_command")
    @mock.patch("lib.gluster.lib.ip_address")
    def test(self, _ip_address, _run_command):
        _run_command.return_value = Ok("172.217.3.206\n")
        _ip_address.return_value = ip_address("172.217.3.206")
        result = lib.resolve_to_ip("google.com")
        _ip_address.assert_called_with(address="172.217.3.206")
        self.assertTrue(result.is_ok())
        self.assertTrue(result.value == ip_address("172.217.3.206"))

    @mock.patch("lib.gluster.lib.get_host_ip")
    def testLocalhost(self, _get_host_ip):
        _get_host_ip.return_value = "192.168.1.2"
        result = lib.resolve_to_ip("localhost")
        self.assertTrue(result.is_ok())
        self.assertTrue(result.value == ip_address("192.168.1.2"))


class TestGetLocalIp(unittest.TestCase):
    @mock.patch("lib.gluster.lib.unit_get")
    @mock.patch("lib.gluster.lib.get_host_ip")
    def testGetLocalIp(self, _get_host_ip, _unit_get):
        _unit_get.return_value = "192.168.1.6"
        _get_host_ip.return_value = "192.168.1.6"
        result = lib.get_local_ip()
        self.assertTrue(result.is_ok())
        self.assertTrue(result.value == ip_address("192.168.1.6"))


class TestTranslateToBytes(unittest.TestCase):
    def setUp(self):
        self.tests = {
            "1TB": 1099511627776.0,
            "8.2KB": 8396.8,
            "2Bytes": 2.0
        }

    def test(self):
        for test, correct in self.tests.items():
            self.assertEqual(lib.translate_to_bytes(test), correct)

    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()
