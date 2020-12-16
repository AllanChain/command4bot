from command4bot.command import calc_status_diff


def test_one_diff():
    assert calc_status_diff(
        {
            "echo": True,
            "hello": False,
        },
        {
            "echo": True,
            "hello": True,
        },
    ) == {
        "hello": True,
    }


def test_missing_and_diff():
    assert calc_status_diff(
        {
            "echo": True,
            "hello": False,
        },
        {
            "hello": True,
        },
    ) == {
        "hello": True,
    }


def test_same():
    assert not calc_status_diff(
        {
            "echo": True,
            "hello": False,
        },
        {
            "echo": True,
            "hello": False,
        },
    )


def test_new_one():
    assert not calc_status_diff(
        {
            "echo": True,
        },
        {
            "echo": True,
            "hello": True,
        },
    )


def test_new_one_and_diff():
    assert calc_status_diff(
        {
            "echo": True,
        },
        {
            "echo": False,
            "hello": True,
        },
    ) == {
        "echo": False,
    }


def test_all_diff():
    assert calc_status_diff(
        {
            "echo": True,
            "hello": False,
        },
        {
            "echo": False,
            "hello": True,
        },
    ) == {
        "echo": False,
        "hello": True,
    }
