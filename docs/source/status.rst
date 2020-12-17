Managing Status
===============

Registering a command handler with a decorator and taking effect is cool, but it's not always the case. Sometimes you may want to disable a command temporarily, or dynamically, without changing the source code. That's when command status management becomes handy.

Closing and Opening Commands
----------------------------

Given a command ``greet``

.. code-block:: python

    @mgr.command
    def greet():
        return "Hello!"

To disable or close it, just call :meth"`CommandsManager.close`

.. code-block:: python

    mgr.close("greet")

.. note::
    You should implement your own logic when to close and open commands. For example, check whether the user is granted to do so.

When attempting to execute a closed command, the comamnd handler will not be called, and the execution just returns :attr:`Config.text_command_closed`.

.. code-block:: python

    >>> mgr.exec("greet")
    'Sorry, this command is currently disabled.'

.. note::
    Pass the name to :meth:`CommandsManager.close`, not the command handler function.

Opening a command using :meth"`CommandsManager.open` is the same:

.. code-block:: python

    mgr.open("greet")

Introducing Command Registry
----------------------------

Internally, command status and registry is managed in :class:`BaseCommandRegistry`. By default, :class:`CommandsManager` will use :class:`CommandRegistry`, which implements a in-memory registry.

Marking Default Closed
----------------------

Sometimes a command is more often closed than open. So it's better to let it be closed until it's time to open it. That's what :meth:`BaseCommandRegistry.mark_default_closed` does.

.. note::
    Why implemented in :class:`BaseCommandRegistry` instead of :class:`CommandsManager`? Because marking default closed is completely a registry's feature, while taking action to actually open and close commands involves updating :class:`Context` 's reference count.

You can either use it as a decorator or just call it with command names. But make sure mark it close **before** registering the command handler. That's because on registering, :class:`Context` 's reference count will be updated based on the status. You will get a ``ValueError`` if trying to mark after registering the command.

.. code-block:: python

    @mgr.command
    @mgr.command_reg.mark_default_closed
    def hidden(payload):
        return f"You found {payload}"

    mgr.command_reg.mark_default_closed("hello")

    @mgr.command(groups=["hello"])
    def hi():
        return "hi!"

    @mgr.command(groups=["hello"])
    def aloha():
        return "aloha!"
