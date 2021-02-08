import pytest

from command4bot import CommandsManager


class TestInsensitive:
    @pytest.fixture(scope="class")
    def mgr(self):
        mgr = CommandsManager(command_case_sensitive=False)

        @mgr.command
        def hEllo():
            return "hi"

        return mgr

    @pytest.mark.parametrize("cmd", ["Hello", "hello", "HeLLo"])
    def test_invoke(self, mgr: CommandsManager, cmd: str):
        assert mgr.exec(cmd) == "hi"

    def test_register_keyword_equal(self, mgr: CommandsManager):
        with pytest.raises(ValueError) as e_info:

            @mgr.command
            def hello():
                return "aloha"

        e_message = e_info.value.args[0].lower()
        assert "command keyword" in e_message

    def test_register_name_equal(self, mgr: CommandsManager):
        try:

            @mgr.command(keywords=["aloha"])
            def hello():
                return "aloha"

        except ValueError as e:
            pytest.fail(f"Did raise {e}")


class TestSensitive:
    @pytest.fixture(scope="class")
    def mgr(self):
        mgr = CommandsManager()

        @mgr.command
        def hEllo():
            return "hi"

        return mgr

    def test_invoke(self, mgr: CommandsManager):
        assert "hEllo" in mgr.exec("hello")
