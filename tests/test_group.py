import pytest

from command4bot import CommandsManager
from command4bot.manager import DEFAULT_CONFIG


class TestGroupClose:
    @pytest.fixture(scope="class")
    def mgr(self):
        mgr = CommandsManager()

        @mgr.command(groups=["hello"])
        def hi():
            return "hi"

        @mgr.command(groups=["hello"])
        def aloha():
            return "aloha"

        return mgr

    @pytest.fixture(scope="class", autouse=True)
    def close_group(self, mgr: CommandsManager):
        mgr.close("hello")

    def test_close_both(self, mgr):
        assert mgr.exec("hi") == DEFAULT_CONFIG["text_command_closed"]
        assert mgr.exec("aloha") == DEFAULT_CONFIG["text_command_closed"]


class TestGroupOpen:
    @pytest.fixture(scope="class")
    def mgr(self):
        mgr = CommandsManager()
        mgr.command_reg.mark_default_closed("hello")

        @mgr.command(groups=["hello"])
        def hi():
            return "hi"

        @mgr.command(groups=["hello"])
        def aloha():
            return "aloha"

        return mgr

    @pytest.fixture(scope="class")
    def open_group(self, mgr: CommandsManager):
        mgr.open("hello")

    def test_default_close(self, mgr):
        assert mgr.exec("hi") == DEFAULT_CONFIG["text_command_closed"]
        assert mgr.exec("aloha") == DEFAULT_CONFIG["text_command_closed"]

    def test_open_both(self, mgr, open_group):
        assert mgr.exec("hi") == "hi"
        assert mgr.exec("aloha") == "aloha"
