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
