import pytest

from command4bot import CommandsManager


@pytest.fixture()
def mgr():
    return CommandsManager()


class TestDuplicate:
    def test_duplicate_command_name(self, mgr: CommandsManager):
        @mgr.command(keywords=("kwa",))
        def dupcmd():
            pass

        with pytest.raises(ValueError) as e_info:

            @mgr.command(keywords=("kwb",))
            def dupcmd():  # NOQA
                pass

        e_message = e_info.value.args[0].lower()
        assert "name" in e_message and "dupcmd" in e_message

    def test_duplicate_command_name_and_group(self, mgr: CommandsManager):
        with pytest.raises(ValueError) as e_info:

            @mgr.command(groups=["dupcmd"])
            def dupcmd():
                pass

        e_message = e_info.value.args[0].lower()
        assert "name" in e_message and "dupcmd" in e_message

    def test_duplicate_command_keyword(self, mgr: CommandsManager):
        @mgr.command(keywords=("kw",))
        def cmda():
            pass

        with pytest.raises(ValueError) as e_info:

            @mgr.command(keywords=("kw",))
            def cmdb():
                pass

        e_message = e_info.value.args[0].lower()
        assert "keyword" in e_message and "kw" in e_message

    def test_duplicate_setup(self, mgr: CommandsManager):
        @mgr.setup
        def setdup():
            pass

        with pytest.raises(ValueError) as e_info:

            @mgr.setup
            def setdup():  # NOQA
                pass

        e_message = e_info.value.args[0].lower()
        assert "setup" in e_message and "setdup" in e_message


class TestNotFound:
    def test_setup_not_found(self, mgr: CommandsManager):
        with pytest.raises(ValueError) as e_info:

            @mgr.command
            def hello(world):
                pass

        e_message = e_info.value.args[0].lower()
        assert "setup" in e_message and "world" in e_message
