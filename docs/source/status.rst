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

To disable or close it, just call

.. code-block:: python

    mgr.close("greet")

When attempting to execute a closed command, the comamnd handler will not be called, and the execution just returns ``"CLOSED"``.

.. code-block:: python

    >>> mgr.exec("greet")
    'CLOSED'

.. note::
    Pass the name to :meth:`CommandsManager.close`, not the command handler function.
