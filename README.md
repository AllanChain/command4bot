# Command For Bot

![PyPI](https://img.shields.io/pypi/v/command4bot)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/command4bot)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/command4bot)

![Run Tests](https://github.com/AllanChain/command4bot/workflows/Run%20Tests/badge.svg)
[![codecov](https://codecov.io/gh/AllanChain/command4bot/branch/master/graph/badge.svg?token=RJV7MMZC5D)](https://codecov.io/gh/AllanChain/command4bot)

![Libraries.io dependency status for GitHub repo](https://img.shields.io/librariesio/github/AllanChain/command4bot)
![GitHub last commit](https://img.shields.io/github/last-commit/AllanChain/command4bot)
![PyPI - Downloads](https://img.shields.io/pypi/dm/command4bot)

![Check Code Style](https://github.com/AllanChain/command4bot/workflows/Check%20Code%20Style/badge.svg)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

`command4bot` is a general purpose library for command-based iteraction made for bots.

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Features](#features)
- [Documentation](#documentation)
- [Todo](#todo)

## Installation

```shell
pip install command4bot
```

## Quick Start

```python
from command4bot import CommandsManager

mgr = CommandsManager()

@mgr.command
def greet(payload):
    return f"Hello, {payload}!"

mgr.exec('greet John')  # 'Hello, John!'
```

## Features

- Register command with a simple decorator
- Managing command open and closed status with ease
- Automatically manage command's dependency (a.k.a. `setup`) with its status
- Fallback handlers if no command found

## Documentation

:warning: The documentation is still working in progress!

<https://command4bot.readthedocs.io/en/latest/>

## Todo

- [ ] Support for commands need interaction
