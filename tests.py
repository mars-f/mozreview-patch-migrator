# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import migrate

@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")


def test_binary_patch_saving(tmpdir):
    tmpdir.ensure('1', dir=True)
    data = migrate.DiffData(1, 1, b'111')
    migrate.save_patch(data, str(tmpdir))
