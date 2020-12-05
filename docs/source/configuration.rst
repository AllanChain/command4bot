.. module:: command4bot

Configuration
=============

How to Config
-------------

It is possible to config :class:`CommandsManager` when creating the instance.

.. code-block:: python

    mgr = CommandsManager(config={
        "text_general_response": "Yes, Sir!"
    })
    # Or
    mgr = CommandsManager(
        text_general_response = "Yes, Sir!"
    )


Configuration Reference
-----------------------

.. autoclass:: Config
    :members:
