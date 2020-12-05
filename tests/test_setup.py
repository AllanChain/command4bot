import pytest

from command4bot import CommandsManager


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
        mgr = CommandsManager()
        data_share.status = None

        @mgr.setup
        def data():
            data_share.status = "pending"
            yield "abc"
            data_share.status = "done"

        @mgr.command()
        @mgr.command_reg.mark_default_closed
        def post(data):
            return data

        return mgr

    @pytest.fixture(scope="class")
    def open_post(self, mgr):
        mgr.open("post")

    def test_not_inited_if_command_closed(
        self, mgr: CommandsManager, data_share
    ):
        assert data_share.status is None
        assert mgr.setup_reg.get("data").cached_generator is None
        assert mgr.setup_reg.get("data").cached_value is None
        assert not mgr.setup_reg.get("data").is_cached

    def test_lazy_load(self, mgr, open_post, data_share):
        assert data_share.status is None

    def test_value_cached(self, mgr: CommandsManager, open_post):
        assert mgr.exec("post") == "abc"
        assert mgr.setup_reg.get("data").cached_generator
        assert mgr.setup_reg.get("data").cached_value
        assert mgr.setup_reg.get("data").is_cached
        assert mgr.exec("post") == "abc"  # cache properly


class TestNoCache:
    @pytest.fixture(scope="class")
    def mgr(self, data_share):
        mgr = CommandsManager()
        data_share.run_count = 0

        @mgr.setup(enable_cache=False)
        def data():
            data_share.run_count += 1
            yield data_share.run_count

        @mgr.command
        def post(data):
            return data

        mgr.exec("post")
        return mgr

    def test_not_cached(self, mgr: CommandsManager):
        assert not mgr.setup_reg.get("data").is_cached
        assert mgr.setup_reg.get("data").cached_value is None
        assert mgr.setup_reg.get("data").cached_generator is None

    def test_run_twice(self, mgr: CommandsManager, data_share):
        assert mgr.exec("post") == 2
        assert data_share.run_count == 2


class TestRunCount:
    @pytest.fixture(scope="class")
    def mgr(self, data_share):
        mgr = CommandsManager()
        data_share.run_count = 0

        @mgr.setup
        def data():
            data_share.run_count += 1
            yield data_share.run_count

        @mgr.command
        def post(data):
            return data

        mgr.exec("post")
        return mgr

    def test_run_twice(self, mgr: CommandsManager, data_share):
        assert mgr.exec("post") == 1
        assert data_share.run_count == 1


class TestGeneratorSetupCleanup:
    @pytest.fixture(scope="class")
    def mgr(self, data_share):
        mgr = CommandsManager()

        @mgr.setup
        def data():
            data_share.status = "pending"
            yield "abc"
            data_share.status = "done"

        @mgr.command
        def post(data):
            return data

        mgr.exec("post")
        mgr.close("post")
        return mgr

    def test_cleanup(self, mgr: CommandsManager, data_share):
        assert data_share.status == "done"
        assert mgr.setup_reg.get("data").cached_generator is None
        assert mgr.setup_reg.get("data").cached_value is None
        assert not mgr.setup_reg.get("data").is_cached
