import pytest

from command4bot import CommandsManager


class TestBasicContext:
    @pytest.fixture(scope="class")
    def mgr(self):
        mgr = CommandsManager()

        @mgr.context
        def ws_data():
            return {"content": "abc"}

        @mgr.context()
        def ws_client():
            return {"send": lambda x: x}

        @mgr.command()
        def send(ws_client, ws_data):
            return ws_client["send"](ws_data["content"])

        return mgr

    def test_context(self, mgr: CommandsManager):
        assert mgr.exec("send") == "abc"


class TestGeneratorContext:
    @pytest.fixture(scope="class")
    def mgr(self, data_share):
        mgr = CommandsManager()
        data_share.status = None

        @mgr.context
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
    def open_post(self, mgr: CommandsManager):
        mgr.open("post")

    def test_not_inited_if_command_closed(
        self, mgr: CommandsManager, data_share
    ):
        assert data_share.status is None
        assert mgr.context_reg.get("data").cached_generator is None
        assert mgr.context_reg.get("data").cached_value is None
        assert not mgr.context_reg.get("data").is_cached

    def test_lazy_load(self, mgr, open_post, data_share):
        assert data_share.status is None

    def test_value_cached(self, mgr: CommandsManager, open_post):
        assert mgr.exec("post") == "abc"
        assert mgr.context_reg.get("data").cached_generator
        assert mgr.context_reg.get("data").cached_value
        assert mgr.context_reg.get("data").is_cached
        assert mgr.exec("post") == "abc"  # cache properly


class TestNoCache:
    @pytest.fixture(scope="class")
    def mgr(self, data_share):
        mgr = CommandsManager()
        data_share.run_count = 0

        @mgr.context(enable_cache=False)
        def data():
            data_share.run_count += 1
            yield data_share.run_count

        @mgr.command
        def post(data):
            return data

        mgr.exec("post")
        return mgr

    def test_not_cached(self, mgr: CommandsManager):
        assert not mgr.context_reg.get("data").is_cached
        assert mgr.context_reg.get("data").cached_value is None
        assert mgr.context_reg.get("data").cached_generator is None

    def test_run_twice(self, mgr: CommandsManager, data_share):
        assert mgr.exec("post") == 2
        assert data_share.run_count == 2


class TestRunCount:
    @pytest.fixture(scope="class")
    def mgr(self, data_share):
        mgr = CommandsManager()
        data_share.run_count = 0

        @mgr.context
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


class TestGeneratorContextCleanup:
    @pytest.fixture(scope="class")
    def mgr(self, data_share):
        mgr = CommandsManager()

        @mgr.context
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
        assert mgr.context_reg.get("data").cached_generator is None
        assert mgr.context_reg.get("data").cached_value is None
        assert not mgr.context_reg.get("data").is_cached


class TestContextOpenError:
    @pytest.fixture(scope="class")
    def mgr(self):
        mgr = CommandsManager()

        @mgr.context
        def data():
            raise ValueError("This context will always fail")

        @mgr.command
        def post(data):
            return data

        return mgr

    def test_raises(self, mgr: CommandsManager):
        with pytest.raises(ValueError):
            mgr.exec("post")

    def test_reference(self, mgr: CommandsManager):
        mgr.close("post")
        assert mgr.context_reg.get("data").reference_count == 0
        mgr.close("post")
        assert mgr.context_reg.get("data").reference_count == 0


class TestContextCloseError:
    @pytest.fixture(scope="class")
    def mgr(self):
        mgr = CommandsManager()

        @mgr.context
        def data():
            yield "abc"
            raise ValueError("This context will always fail")

        @mgr.command
        def post(data):
            return data

        mgr.exec("post")
        return mgr

    # @pytest.mark.parametrize("run", [1, 2])  # test close twice
    def test_reference(self, mgr: CommandsManager):  # , run: int):
        with pytest.raises(ValueError):
            mgr.close("post")
        assert mgr.context_reg.get("data").reference_count == 0
        mgr.close("post")
        assert mgr.context_reg.get("data").reference_count == 0
