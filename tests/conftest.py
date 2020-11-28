from types import SimpleNamespace

import pytest


@pytest.fixture(scope="class")
def data_share():
    return SimpleNamespace()
