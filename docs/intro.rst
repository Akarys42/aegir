Introduction
============

This system articulates around configuration entries, subclassing :class:`aegir.ConfigEntry`, being class that have attributes that can be automatically overridden by a configuration file.

Here is an example of a configuration entry:

.. code-block:: python

   # file: my_app/example.py
   from aegir import ConfigEntry

   class MyEntry(ConfigEntry):
      my_str: str = "default_value"
      my_int: int = 42

You are able to access those attributes normally:

.. code-block:: python

   >>> from my_app.example import MyEntry
   >>> MyEntry.my_str
   "default_value"
   >>> MyEntry.my_int
   42

You are now also able to load a configuration file, using the :func:`aegir.load` function. This function will override entries based on the dotted path to the module of the entry.

Using the example above, the configuration file could look like:

.. code-block:: yaml

    # file: my_config.yaml
    my_app.example:
        my_str: "new_value"

The :func:`aegir.load` function will replace those attributes with the ones from the configuration file.

.. code-block:: python

    >>> from aegir import load
    >>> load("my_config.yaml")
    >>> from my_app.example import MyEntry
    >>> MyEntry.my_str
    "new_value"
