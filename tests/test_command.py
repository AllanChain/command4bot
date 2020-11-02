import pytest

from command4bot import CommandsManager


@pytest.fixture(scope="class")
def basic_mgr():
    basic_mgr = CommandsManager(command_needs_blacklist=("message", "payload"))

    @basic_mgr.setup
    def ws():
        ws_client = {"content": "abc"}
        yield ws_client
        print("tear down")

    @basic_mgr.command
    def hello(payload, message):
        return f'hello, {message["source"]}!'

    @basic_mgr.command()
    def send(payload, ws):
        return ws["content"]

    return basic_mgr


class TestBasicUsage:
    def test_custom_args(self, basic_mgr):
        result = basic_mgr.exec("hello", message={"source": "source"})
        assert result == "hello, source!"

    def test_setup(self, basic_mgr):
        assert basic_mgr.exec("send") == "abc"

    def test_fallback(self, basic_mgr):
        assert "send" in basic_mgr.exec("sed")
