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

import unittest

import lsst.utils.tests
from lsst.pex.config import Config, Field, ConfigField, ConfigChoiceField, \
    RegistryField, Registry, ConfigurableField, ConfigurableInstance, \
    ConfigDictField
from lsst.dax.apdb import Apdb, ApdbConfig

from lsst.verify.tasks import ConfigApdbLoader


class ConfigApdbLoaderTestSuite(lsst.utils.tests.TestCase):

    @staticmethod
    def _dummyRegistry():
        class DummyConfigurable:
            ConfigClass = Config
        registry = Registry()
        registry.register("foo", DummyConfigurable)
        registry.register("bar", Apdb, ConfigClass=ApdbConfig)
        return registry

    @staticmethod
    def _dummyApdbConfig():
        config = ApdbConfig()
        config.db_url = "sqlite://"     # in-memory DB
        config.isolation_level = "READ_UNCOMMITTED"
        return config

    def setUp(self):
        self.task = ConfigApdbLoader()

    def testNoConfig(self):
        result = self.task.run(None)
        self.assertIsNone(result.apdb)

    def testEmptyConfig(self):
        result = self.task.run(Config())
        self.assertIsNone(result.apdb)

    def testSelfConfig(self):
        result = self.task.run(self._dummyApdbConfig())
        self.assertIsInstance(result.apdb, Apdb)

    def testConfigChoiceFieldUnSelected(self):
        typemap = {"foo": Config, "bar": ApdbConfig}

        class TestConfig(Config):
            field = ConfigChoiceField(typemap=typemap, doc="")

        config = TestConfig()
        config.field = "foo"
        result = self.task.run(config)
        self.assertIsNone(result.apdb)

    def testConfigChoiceFieldSelected(self):
        typemap = {"foo": Config, "bar": ApdbConfig}

        class TestConfig(Config):
            field = ConfigChoiceField(typemap=typemap, doc="")

        config = TestConfig()
        config.field = "bar"
        config.field["bar"] = self._dummyApdbConfig()
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)

    def testConfigChoiceFieldMulti(self):
        typemap = {"foo": Config, "bar": ApdbConfig}

        class TestConfig(Config):
            field = ConfigChoiceField(typemap=typemap, doc="", multi=True)

        config = TestConfig()
        config.field = {"bar", "foo"}
        config.field["bar"] = self._dummyApdbConfig()
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)

    def testRegistryFieldUnSelected(self):
        registry = self._dummyRegistry()

        class TestConfig(Config):
            field = RegistryField(registry=registry, doc="")

        config = TestConfig()
        config.field = "foo"
        result = self.task.run(config)
        self.assertIsNone(result.apdb)

    def testRegistryFieldSelected(self):
        registry = self._dummyRegistry()

        class TestConfig(Config):
            field = RegistryField(registry=registry, doc="")

        config = TestConfig()
        config.field = "bar"
        config.field["bar"] = self._dummyApdbConfig()
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)

    def testRegistryFieldMulti(self):
        registry = self._dummyRegistry()

        class TestConfig(Config):
            field = RegistryField(registry=registry, doc="", multi=True)

        config = TestConfig()
        config.field = {"bar", "foo"}
        config.field["bar"] = self._dummyApdbConfig()
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)

    def testConfigField(self):
        class TestConfig(Config):
            field = ConfigField(dtype=ApdbConfig,
                                default=self._dummyApdbConfig(), doc="")

        result = self.task.run(TestConfig())
        self.assertIsInstance(result.apdb, Apdb)

    def testConfigurableField(self):
        class TestConfig(Config):
            field = ConfigurableField(target=Apdb, ConfigClass=ApdbConfig,
                                      doc="")

        config = TestConfig()
        config.field = self._dummyApdbConfig()
        self.assertIsInstance(config.field, ConfigurableInstance)
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)

    def testConfigDictFieldUnSelected(self):
        class TestConfig(Config):
            field = ConfigDictField(keytype=int, itemtype=ApdbConfig, doc="")

        result = self.task.run(TestConfig())
        self.assertIsNone(result.apdb)

    def testConfigDictFieldSelected(self):
        class TestConfig(Config):
            field = ConfigDictField(keytype=int, itemtype=ApdbConfig, doc="")

        config = TestConfig()
        config.field = {42: self._dummyApdbConfig()}
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)

    def testSiblingConfigs(self):
        class TestConfig(Config):
            field1 = Field(dtype=int, doc="")
            field2 = ConfigField(dtype=ApdbConfig,
                                 default=self._dummyApdbConfig(), doc="")
            field3 = Field(dtype=str, doc="")

        result = self.task.run(TestConfig())
        self.assertIsInstance(result.apdb, Apdb)

    def testNestedConfigs(self):
        class InnerConfig(Config):
            field = ConfigurableField(target=Apdb,
                                      ConfigClass=ApdbConfig, doc="")

        class TestConfig(Config):
            field = ConfigField(dtype=InnerConfig, doc="")

        config = TestConfig()
        config.field.field = self._dummyApdbConfig()
        self.assertIsInstance(config.field.field, ConfigurableInstance)
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
