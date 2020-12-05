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


class TestDisableDefault:
    @pytest.fixture(scope="class")
    def mgr(self):
        mgr = CommandsManager(config=dict(enable_default_fallback=False))
        return mgr

    def test_exec(self, mgr):
        assert mgr.exec("hello") is None


class TestMultiFallback:
    @pytest.fixture(scope="class")
    def mgr(self, data_share):
        mgr = CommandsManager(config=dict(enable_default_fallback=False))
        data_share.calls = []

        @mgr.fallback(priority=10)
        def fallback10(content):
            data_share.calls.append(10)
            return None

        @mgr.fallback(priority=2)
        def fallback2(content):
            data_share.calls.append(2)
            return "Hey!"

        @mgr.fallback(priority=5)
        def fallback5(content):
            data_share.calls.append(5)
            return None

        return mgr

    @pytest.fixture(scope="class")
    def exec_result(self, mgr):
        return mgr.exec("hello")

    def test_multi(delf, exec_result):
        assert exec_result == "Hey!"

    def test_priority(self, data_share):
        assert data_share.calls == [10, 5, 2]
