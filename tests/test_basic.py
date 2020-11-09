import pytest

from command4bot import CommandsManager


class TestBasicUsage:
    @pytest.fixture(scope="class")
    def mgr(self):
        mgr = CommandsManager(command_needs_ignore=["message"])

        @mgr.command
        def hello(message):
            return f'hello, {message["source"]}!'

        @mgr.command
        def world():
            "Say world"
            return "world"

        return mgr

    def test_simple(self, mgr):
        assert mgr.exec("world") == "world"

    def test_custom_args(self, mgr):
        result = mgr.exec("hello", message={"source": "source"})
        assert result == "hello, source!"

    def test_fallback(self, mgr):
        "This tests both two types of help and cached fallback"
        assert mgr.exec("word") == "Get!\nPossible:\n- Say world"
        assert mgr.exec("adflj") == "Get!"
