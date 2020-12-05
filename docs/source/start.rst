.. module:: command4bot

Quick Start
===========

.. code-block:: python

    from command4bot import CommandsManager

    mgr = CommandsManager()

    @mgr.command
    def greet(payload):
        return f"Hello, {payload}!"

    mgr.exec('greet John')  # 'Hello, John!'


Basic Concepts and Usage
------------------------

.. tip::
    Text in, anything out.

Text Input
^^^^^^^^^^

Or ``content``, is what ever passed to :meth:`CommandsManager.exec`.


Command
^^^^^^^

A command handler is a function to do the actual task.

For example, given text input ``"greet John"``,
the ``mgr`` first finds out that ``greet`` command handler is responsible for this.
Then the ``mgr`` trims ``"greet "`` off and passes ``"John"`` to ``greet`` function.

... note:
    The command handler should be registered with
    :meth:`CommandsManager.command` decorator before taking effect.

    And the argument name must be ``payload``, though can be configured.


Command Status
^^^^^^^^^^^^^^

A command can be either closed or open.
If the command is closed, the command handler will never be called until you open it again.

By default, the command is open after registration.

Setup (Command Dependency)
^^^^^^^^^^^^^^^^^^^^^^^^^^

Command dependencies is trivial to manage if the command is always open.

For example, setup web socket connection if any command needs, and close the connection if all commands need the socket are closed.

.. code-block:: python

    @mgr.setup
    def ws():
        ws_client = WSClient('localhost:8888')
        yield ws_client
        ws_client.close()

    @mgr.command
    def send(paload, ws):
        ws.send(payload)

Fallback
^^^^^^^^
