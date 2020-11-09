import pytest

from command4bot import CommandsManager


class TestOpenClose:
    @pytest.fixture(scope="class")
    def mgr(self):
        mgr = CommandsManager()

        @mgr.setup
        def name():
            return "Jack"

        @mgr.setup
        def haha():
            return "Haha"

        @mgr.command
        def echo(payload, name):
            return f"{name} says {payload}"

        @mgr.command(default_closed=True)
        def hidden(payload, haha):
            return f"{haha}! You found {payload}"

        return mgr

    @pytest.fixture(scope="class")
    def close_echo(self, mgr):
        mgr.close("echo")

    @pytest.fixture(scope="class")
    def open_hidden(self, mgr):
        mgr.open("hidden")

    def test_open_reference_count(self, mgr: CommandsManager):
        assert mgr.setup_reg.get("name").reference_count == 1

    def test_closed_reference_count(self, mgr: CommandsManager):
        assert mgr.setup_reg.get("haha").reference_count == 0

    def test_opening_command_work(self, mgr: CommandsManager):
        assert mgr.exec("echo hello") == "Jack says hello"

    def test_closed_command_closed(self, mgr: CommandsManager):
        assert mgr.exec("hidden treasure") == "CLOSED"

    def test_close_command_status(self, mgr: CommandsManager, close_echo):
        assert not mgr.command_reg.get_status("echo")

    def test_close_command_decrease_reference(
        self, mgr: CommandsManager, close_echo
    ):
        assert mgr.setup_reg.get("name").reference_count == 0

    def test_close_command_cleanup_setup(
        self, mgr: CommandsManager, close_echo
    ):
        assert mgr.setup_reg.get("name").cached_value is None
        assert not mgr.setup_reg.get("name").is_cached

    def test_close_command_not_invokable(
        self, mgr: CommandsManager, close_echo
    ):
        assert mgr.exec("echo hello") == "CLOSED"

    def test_open_command_status(self, mgr: CommandsManager, open_hidden):
        assert mgr.command_reg.get_status("hidden")

    def test_open_command_increase_reference(
        self, mgr: CommandsManager, open_hidden
    ):
        assert mgr.setup_reg.get("haha").reference_count == 1

    def test_open_command_invokable(self, mgr: CommandsManager, open_hidden):
        assert mgr.exec("hidden treasure") == "Haha! You found treasure"
