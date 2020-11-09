import pytest

from command4bot import CommandsManager


class TestFallback:
    @pytest.fixture(scope="class")
    def mgr(self):
        mgr = CommandsManager()

        @mgr.fallback
        def uhoh(content):
            return f'Cannot respond to "{content}"'

        return mgr

    def test_fallback(self, mgr: CommandsManager):
        assert mgr.exec("hello") == 'Cannot respond to "hello"'

    def test_frozen_after_exec(self, mgr: CommandsManager):
        with pytest.raises(ValueError) as e_info:

            @mgr.fallback
            def haha(content):
                return "You will never see this"

        e_message = e_info.value.args[0].lower()
        assert "frozen" in e_message
