# Command For Bot

![Run Tests](https://github.com/AllanChain/command4bot/workflows/Run%20Tests/badge.svg)
![Check Code Style](https://github.com/AllanChain/command4bot/workflows/Check%20Code%20Style/badge.svg)
[![codecov](https://codecov.io/gh/AllanChain/command4bot/branch/master/graph/badge.svg?token=RJV7MMZC5D)](https://codecov.io/gh/AllanChain/command4bot)

:warning: The document is still working in progress!

`command4bot` is a general purpose library for command-based iteraction made for bots, with command registry, command dependency (a.k.a. `setup`), ability to enable / disable commands, fallback functions included.

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Basic Concepts and Usage](#basic-concepts-and-usage)
  - [Command](#command)
  - [Setup (Command Dependency)](#setup-command-dependency)
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

## Basic Concepts and Usage

### Command

Command is a function taking a positional argument (`payload`) and optional keyword arguments.

### Setup (Command Dependency)

Command dependencies is trivial to manage if the command is always open.

For example, setup web socket connection if any command needs, and close the connection if all commands need the socket are closed.

```python
@mgr.setup
def ws():
    ws_client = WSClient('localhost:8888')
    yield ws_client
    ws_client.close()

@mgr.command
def send(paload, ws):
    ws.send(payload)
```


## Todo

- [ ] Support for commands need interaction
