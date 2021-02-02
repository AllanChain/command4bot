import threading
import time
from typing import Callable

import pytest

from command4bot import CommandRegistry, CommandsManager


def thread_execute(target: Callable, count: int):
    threads = [threading.Thread(target=target) for _ in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()  # .join() blocks until thread finish


class TestOpenClose:
    @pytest.fixture(scope="class")
    def mgr(self):
        class SlowCommandRegistry(CommandRegistry):
            def set_status(self, name: str, status: bool) -> None:
                time.sleep(0.1)
                return super().set_status(name, status)

        mgr = CommandsManager(command_reg=SlowCommandRegistry())

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

    @pytest.fixture(scope="class")
    def close_echo(self, mgr: CommandsManager):
        thread_execute(lambda: mgr.close("echo"), 2)

    @pytest.fixture(scope="class")
    def open_hidden(self, mgr: CommandsManager):
        thread_execute(lambda: mgr.open("hidden"), 2)

    def test_close_command_decrease_reference(
        self, mgr: CommandsManager, close_echo
    ):
        assert mgr.context_reg.get("name").reference_count == 0

    def test_open_command_increase_reference(
        self, mgr: CommandsManager, open_hidden
    ):
        assert mgr.context_reg.get("haha").reference_count == 1


class TestContextExecuteOnce:
    @pytest.fixture(scope="class")
    def mgr(self, data_share):
        mgr = CommandsManager()
        data_share.open_count = []
        data_share.close_count = []

        @mgr.context
        def data():
            time.sleep(0.1)
            data_share.open_count.append(42)
            yield "abc"
            time.sleep(0.1)
            data_share.close_count.append(42)

        @mgr.command()
        def post(data):
            return data

        return mgr

    @pytest.fixture(scope="class")
    def exec_post(self, mgr: CommandsManager):
        thread_execute(lambda: mgr.exec("post"), 2)

    @pytest.fixture(scope="class")
    def close_post(self, mgr: CommandsManager):
        thread_execute(lambda: mgr.close("post"), 2)

    def test_setup_once(self, mgr: CommandsManager, exec_post, data_share):
        assert len(data_share.open_count) == 1
        assert mgr.context_reg.get("data").is_cached

    def test_cleanup_once(self, mgr: CommandsManager, close_post, data_share):
        assert len(data_share.close_count) == 1
        assert not mgr.context_reg.get("data").is_cached
