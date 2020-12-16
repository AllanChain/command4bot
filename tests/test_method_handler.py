import pytest

from command4bot import CommandsManager

mgr = CommandsManager()


class TestMethodHandler:
    @pytest.fixture(scope="class", autouse=True)
    def init(self):
        mgr.context(self.data)
        mgr.command(self.tell)
        mgr.fallback(self.fallback)

    def data(self):
        return "truth"

    def tell(self, payload, data):
        return f"tell {payload} {data}"

    def fallback(self, content):
        return f"unknown {content}"

    def test_command_and_context(self):
        assert mgr.exec("tell me") == "tell me truth"

    def test_fallback(self):
        assert mgr.exec("char") == "unknown char"
