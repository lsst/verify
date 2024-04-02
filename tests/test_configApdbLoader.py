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

import shutil
import tempfile
import unittest

import lsst.utils.tests
from lsst.pex.config import Config, Field, ConfigField, ConfigChoiceField, \
    RegistryField, Registry, ConfigurableField, ConfigurableInstance, \
    ConfigDictField
from lsst.dax.apdb import Apdb, ApdbConfig, ApdbSql, ApdbSqlConfig

from lsst.verify.tasks import ConfigApdbLoader


class ConfigApdbLoaderTestSuite(lsst.utils.tests.TestCase):

    @staticmethod
    def _dummyRegistry():
        class DummyConfigurable:
            ConfigClass = Config
        registry = Registry()
        registry.register("foo", DummyConfigurable)
        registry.register("bar", ApdbSql, ConfigClass=ApdbSqlConfig)
        return registry

    def _dummyApdbConfig(self):
        return ApdbSql.init_database(db_url=self.db_url)

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.db_url = f"sqlite:///{self.tempdir}/apdb.sqlite3"
        self.task = ConfigApdbLoader()

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def testEmptyConfig(self):
        result = self.task.run(Config())
        self.assertIsNone(result.apdb)

    def testSelfConfig(self):
        result = self.task.run(self._dummyApdbConfig())
        self.assertIsInstance(result.apdb, Apdb)

    def testConfigChoiceFieldUnSelected(self):
        typemap = {"foo": Config, "bar": ApdbConfig}

        class TestConfig(Config):
            field = ConfigChoiceField(typemap=typemap, doc="test")

        config = TestConfig()
        config.field = "foo"
        result = self.task.run(config)
        self.assertIsNone(result.apdb)

    def testConfigChoiceFieldSelected(self):
        # Note: ConfigChoiceField does not support polymorphic types and it is
        # not very useful for ApdbConfig and subclasses.
        typemap = {"foo": Config, "bar": ApdbSqlConfig}

        class TestConfig(Config):
            field = ConfigChoiceField(typemap=typemap, doc="test")

        config = TestConfig()
        config.field = "bar"
        config.field["bar"] = self._dummyApdbConfig()
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)

    def testConfigChoiceFieldMulti(self):
        # Note: ConfigChoiceField does not support polymorphic types and it is
        # not very useful for ApdbConfig and subclasses.
        typemap = {"foo": Config, "bar": ApdbSqlConfig}

        class TestConfig(Config):
            field = ConfigChoiceField(typemap=typemap, doc="test", multi=True)

        config = TestConfig()
        config.field = {"bar", "foo"}
        config.field["bar"] = self._dummyApdbConfig()
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)

    def testRegistryFieldUnSelected(self):
        registry = self._dummyRegistry()

        class TestConfig(Config):
            field = RegistryField(registry=registry, doc="test")

        config = TestConfig()
        config.field = "foo"
        result = self.task.run(config)
        self.assertIsNone(result.apdb)

    def testRegistryFieldSelected(self):
        registry = self._dummyRegistry()

        class TestConfig(Config):
            field = RegistryField(registry=registry, doc="test")

        config = TestConfig()
        config.field = "bar"
        config.field["bar"] = self._dummyApdbConfig()
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)

    def testRegistryFieldMulti(self):
        registry = self._dummyRegistry()

        class TestConfig(Config):
            field = RegistryField(registry=registry, doc="test", multi=True)

        config = TestConfig()
        config.field = {"bar", "foo"}
        config.field["bar"] = self._dummyApdbConfig()
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)

    def testConfigField(self):
        # Note: ConfigField does not support polymorphic types and it is not
        # very useful for ApdbConfig and subclasses.
        class TestConfig(Config):
            field = ConfigField(dtype=ApdbSqlConfig,
                                default=self._dummyApdbConfig(), doc="test")

        result = self.task.run(TestConfig())
        self.assertIsInstance(result.apdb, Apdb)

    def testConfigurableField(self):
        class TestConfig(Config):
            field = ConfigurableField(target=ApdbSql, doc="test")

        config = TestConfig()
        config.field = self._dummyApdbConfig()
        self.assertIsInstance(config.field, ConfigurableInstance)
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)

    def testConfigurableFieldRetarget(self):
        # Initally set to abstract target, has to be re-targeted before use.
        class TestConfig(Config):
            field = ConfigurableField(target=Apdb, doc="test")

        config = TestConfig()
        config.field.retarget(ApdbSql)
        config.field = self._dummyApdbConfig()
        self.assertIsInstance(config.field, ConfigurableInstance)
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)

    def testConfigDictFieldUnSelected(self):
        class TestConfig(Config):
            field = ConfigDictField(keytype=int, itemtype=ApdbConfig, doc="test")

        result = self.task.run(TestConfig())
        self.assertIsNone(result.apdb)

    def testConfigDictFieldSelected(self):
        # Note: ConfigDictField does not support polymorphic types and it is
        # not very useful for ApdbConfig and subclasses.
        class TestConfig(Config):
            field = ConfigDictField(keytype=int, itemtype=ApdbSqlConfig,
                                    doc="test")

        config = TestConfig()
        config.field = {42: self._dummyApdbConfig()}
        result = self.task.run(config)
        self.assertIsInstance(result.apdb, Apdb)

    def testSiblingConfigs(self):
        # Note: ConfigField does not support polymorphic types and it is not
        # very useful for ApdbConfig and subclasses.
        class TestConfig(Config):
            field1 = Field(dtype=int, doc="test")
            field2 = ConfigField(dtype=ApdbSqlConfig,
                                 default=self._dummyApdbConfig(), doc="test")
            field3 = Field(dtype=str, doc="test")

        result = self.task.run(TestConfig())
        self.assertIsInstance(result.apdb, Apdb)

    def testNestedConfigs(self):
        class InnerConfig(Config):
            field = ConfigurableField(target=ApdbSql, doc="test")

        class TestConfig(Config):
            field = ConfigField(dtype=InnerConfig, doc="test")

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
