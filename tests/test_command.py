import pytest

from command4bot import CommandsManager


@pytest.fixture(scope="class")
def data_share():
    return {}


class TestBasicUsage:
    @pytest.fixture(scope="class")
    def mgr(self):
        mgr = CommandsManager(command_needs_ignore=["message"])

        @mgr.command
        def hello(message):
            return f'hello, {message["source"]}!'

        @mgr.command
        def world():
            "Say world"
            return "world"

        return mgr

    def test_simple(self, mgr):
        assert mgr.exec("world") == "world"

    def test_custom_args(self, mgr):
        result = mgr.exec("hello", message={"source": "source"})
        assert result == "hello, source!"

    def test_fallback(self, mgr):
        "This tests both two types of help and cached fallback"
        assert mgr.exec("word") == "Get!\nPossible:\n- Say world"
        assert mgr.exec("adflj") == "Get!"


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
        data_share["status"] = None

        @mgr.setup
        def data():
            data_share["status"] = "pending"
            yield "abc"
            data_share["status"] = "done"

        @mgr.command(default_closed=True)
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
