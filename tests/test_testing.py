# Copyright 2020 Akamai Technologies, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from pallas import Athena
from pallas.testing import AthenaFake


@pytest.fixture(name="fake")
def fake_fixture():
    return AthenaFake()


@pytest.fixture(name="athena")
def athena_fixture(fake):
    return Athena(fake)


class TestAthenaFake:
    def test_repr(self, fake):
        assert repr(fake) == "<AthenaFake>"

    def test_submit(self, athena, fake):
        query = athena.submit("SELECT ...")
        assert query.execution_id == "query-1"
        assert fake.request_log == ["StartQueryExecution"]

    def test_submit_multiple(self, athena, fake):
        query1 = athena.submit("SELECT ...")
        query2 = athena.submit("SELECT ...")
        assert query1.execution_id == "query-1"
        assert query2.execution_id == "query-2"
        assert fake.request_log == ["StartQueryExecution", "StartQueryExecution"]

    def test_get_query(self, athena):
        query1 = athena.submit("SELECT ...")
        query2 = athena.get_query("query-1")
        assert query2.execution_id == query1.execution_id

    def test_query_info(self, athena, fake):
        query = athena.submit("SELECT ...")
        fake.request_log.clear()
        info = query.get_info()
        assert info.execution_id == "query-1"
        assert info.sql == "SELECT ..."
        assert info.database is None
        assert info.finished
        assert info.succeeded
        assert fake.request_log == ["GetQueryExecution"]

    def test_query_info_remembered(self, athena, fake):
        query = athena.submit("SELECT ...")
        fake.request_log.clear()
        query.get_info()
        query.get_info()
        assert fake.request_log == ["GetQueryExecution"]

    def test_query_info_remembered_not_shared(self, athena, fake):
        query = athena.submit("SELECT ...")
        fake.request_log.clear()
        query.get_info()
        athena.get_query(query.execution_id).get_info()
        assert fake.request_log == ["GetQueryExecution", "GetQueryExecution"]

    def test_default_query_results(self, athena):
        query = athena.submit("SELECT ...")
        results = query.get_results()
        assert list(results) == []

    def test_custom_query_results(self, athena, fake):
        fake.column_names = "id", "name"
        fake.data = [("1", "foo"), ("2", "bar")]
        query = athena.submit("SELECT ...")
        results = query.get_results()
        assert list(results) == [
            {"id": "1", "name": "foo"},
            {"id": "2", "name": "bar"},
        ]

    def test_custom_query_results_with_custom_types(self, athena, fake):
        fake.column_names = "id", "name"
        fake.column_types = "integer", "varchar"
        fake.data = [("1", "foo"), ("2", "bar")]
        query = athena.submit("SELECT ...")
        results = query.get_results()
        assert list(results) == [
            {"id": 1, "name": "foo"},
            {"id": 2, "name": "bar"},
        ]
