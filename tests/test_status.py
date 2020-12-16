import pytest

from command4bot import CommandsManager
from command4bot.manager import DEFAULT_CONFIG


@pytest.fixture(scope="class")
def mgr():
    mgr = CommandsManager()

    @mgr.context
    def name():
        return "Jack"

    @mgr.context
    def haha():
        return "Haha"

    @mgr.command
    def echo(payload, name):
        return f"{name} says {payload}"

    @mgr.command()
    @mgr.command_reg.mark_default_closed
    def hidden(payload, haha):
        return f"{haha}! You found {payload}"

    return mgr


class TestOpenClose:
    @pytest.fixture(scope="class")
    def close_echo(self, mgr: CommandsManager):
        mgr.close("echo")

    @pytest.fixture(scope="class")
    def open_hidden(self, mgr: CommandsManager):
        mgr.open("hidden")

    def test_open_reference_count(self, mgr: CommandsManager):
        assert mgr.context_reg.get("name").reference_count == 1

    def test_closed_reference_count(self, mgr: CommandsManager):
        assert mgr.context_reg.get("haha").reference_count == 0

    def test_opening_command_work(self, mgr: CommandsManager):
        assert mgr.exec("echo hello") == "Jack says hello"

    def test_closed_command_closed(self, mgr: CommandsManager):
        assert (
            mgr.exec("hidden treasure")
            == DEFAULT_CONFIG["text_command_closed"]
        )

    def test_close_command_status(self, mgr: CommandsManager, close_echo):
        assert not mgr.command_reg.get_status("echo")

    def test_close_command_decrease_reference(
        self, mgr: CommandsManager, close_echo
    ):
        assert mgr.context_reg.get("name").reference_count == 0

    def test_close_command_cleanup_context(
        self, mgr: CommandsManager, close_echo
    ):
        assert mgr.context_reg.get("name").cached_value is None
        assert not mgr.context_reg.get("name").is_cached

    def test_close_command_not_invokable(
        self, mgr: CommandsManager, close_echo
    ):
        assert mgr.exec("echo hello") == DEFAULT_CONFIG["text_command_closed"]

    def test_open_command_status(self, mgr: CommandsManager, open_hidden):
        assert mgr.command_reg.get_status("hidden")

    def test_open_command_increase_reference(
        self, mgr: CommandsManager, open_hidden
    ):
        assert mgr.context_reg.get("haha").reference_count == 1

    def test_open_command_invokable(self, mgr: CommandsManager, open_hidden):
        assert mgr.exec("hidden treasure") == "Haha! You found treasure"


class TestOpenCloseTwice:
    @pytest.fixture(scope="class", autouse=True)
    def setup_mgr(self, mgr: CommandsManager):
        mgr.open("hidden")
        mgr.close("echo")

    def test_open_twice(self, mgr: CommandsManager):
        mgr.open("hidden")
        assert mgr.context_reg.get("haha").reference_count == 1

    def test_close_twice(self, mgr: CommandsManager):
        mgr.close("echo")
        assert mgr.context_reg.get("name").reference_count == 0


class TestBatchUpdate:
    @pytest.fixture(scope="class", autouse=True)
    def batch_update(self, mgr: CommandsManager):
        mgr.batch_update_status({"echo": False, "hidden": True})

    def test_status(self, mgr: CommandsManager):
        assert mgr.exec("echo") == DEFAULT_CONFIG["text_command_closed"]
        assert mgr.exec("hidden treasure") == "Haha! You found treasure"

    def test_reference(self, mgr: CommandsManager):
        assert mgr.context_reg.get("name").reference_count == 0
        assert mgr.context_reg.get("haha").reference_count == 1


class TestStatusDiff:
    @pytest.fixture(scope="class", autouse=True)
    def batch_update(self, mgr: CommandsManager):
        mgr.batch_update_status(
            mgr.command_reg.calc_status_diff(  # type: ignore
                {
                    "echo": True,
                    "hidden": True,
                }
            )
        )

    def test_status(self, mgr: CommandsManager):
        assert mgr.exec("echo hello") == "Jack says hello"
        assert mgr.exec("hidden treasure") == "Haha! You found treasure"

    def test_reference(self, mgr: CommandsManager):
        assert mgr.context_reg.get("name").reference_count == 1
        assert mgr.context_reg.get("haha").reference_count == 1
