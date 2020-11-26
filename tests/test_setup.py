import pytest

from command4bot import CommandRegistry, CommandsManager


class TestBasicSetup:
    @pytest.fixture(scope="class")
    def mgr(self):
        mgr = CommandsManager()

        @mgr.setup
        def ws_data():
            return {"content": "abc"}

        @mgr.setup()
        def ws_client():
            return {"send": lambda x: x}

        @mgr.command()
        def send(ws_client, ws_data):
            return ws_client["send"](ws_data["content"])

        return mgr

    def test_setup(self, mgr):
        assert mgr.exec("send") == "abc"


class TestGeneratorSetup:
    @pytest.fixture(scope="class")
    def mgr(self, data_share):
        command_reg = CommandRegistry()
        mgr = CommandsManager(command_reg=command_reg)
        data_share["status"] = None

        @mgr.setup
        def data():
            data_share["status"] = "pending"
            yield "abc"
            data_share["status"] = "done"

        @mgr.command()
        @command_reg.mark_default_closed
        def post(data):
            return data

        return mgr

    @pytest.fixture(scope="class")
    def open_post(self, mgr):
        mgr.open("post")

    def test_not_inited_if_command_closed(
        self, mgr: CommandsManager, data_share
    ):
        assert data_share["status"] is None
        assert mgr.setup_reg.get("data").cached_generator is None
        assert mgr.setup_reg.get("data").cached_value is None
        assert not mgr.setup_reg.get("data").is_cached

    def test_lazy_load(self, mgr, open_post, data_share):
        assert data_share["status"] is None

    def test_value_cached(self, mgr: CommandsManager, open_post):
        assert mgr.exec("post") == "abc"
        assert mgr.setup_reg.get("data").cached_generator
        assert mgr.setup_reg.get("data").cached_value
        assert mgr.setup_reg.get("data").is_cached


class TestGeneratorSetupCleanup:
    @pytest.fixture(scope="class")
    def mgr(self, data_share):
        mgr = CommandsManager()

        @mgr.setup
        def data():
            data_share["status"] = "pending"
            yield "abc"
            data_share["status"] = "done"

        @mgr.command
        def post(data):
            return data

        mgr.exec("post")
        mgr.close("post")
        return mgr

    def test_cleanup(self, mgr: CommandsManager, data_share):
        assert data_share["status"] == "done"
        assert mgr.setup_reg.get("data").cached_generator is None
        assert mgr.setup_reg.get("data").cached_value is None
        assert not mgr.setup_reg.get("data").is_cached
