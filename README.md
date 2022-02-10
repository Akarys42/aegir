# Aegir

Aegir is a library allowing you to add configuration options to your Python project without any additional work.

# Usage

This system articulates around configuration entries, being class that have attributes that can be automatically overridden by a configuration file.

Here is an example of a configuration entry:

```python
# file: my_app/example.py
from aegir import ConfigEntry

class MyEntry(ConfigEntry):
    my_str: str = "default_value"
    my_int: int = 42
```

You are able to access those attributes normally:

```python
>>> from my_app.example import MyEntry
>>> MyEntry.my_str
"default_value"
>>> MyEntry.my_int
42
```

You are now also able to load a configuration file, using the `load()` function. This function will override entries based on the dotted path to the module of the entry.

Using the example above, the configuration file could look like:
```yaml
# file: my_config.yaml
my_app.example:
  my_str: "new_value"
```

The `load()` function will replace those attributes with the ones from the configuration file.

```python
>>> from aegir import load
>>> load("my_config.yaml")
>>> from my_app.example import MyEntry
>>> MyEntry.my_str
"new_value"
```

## Changing the default path

If you do not wish to use the module path, but rather a custom one, you can use the `path` metaclass argument when creating your instance.

```python
class MyEntry(ConfigEntry, path="custom.path"):
    ...
```

The entry will now be treated as if it was in the `custom.path` module.

## Default arguments

It is possible to not provide default arguements to your configuration entry.

```python
class MyEntry(ConfigEntry):
    without_default: str
```

If the configuration file does not contain the attribute, the `ConfigurationKeyError` exception will be raised. This is useful if you want to make sure that a configuration entry is always present. 

Bear in mind that the configuration file must be loaded before the module containing the entry is created. You can bypass that restriction using the `check_attributes` metaclass argument, such as:

```python
class MyEntry(ConfigEntry, check_attributes=False):
    without_default: str
```

If you wish, you are still able to call `check_attributes()` manually later on to trigger that check.

## !REF constructors

You can use this constructor inside your configuration file to reference another attributes:
```yaml
my_app.example:
  my_str: !REF my_other_entry.my_str
```

# API documentation

For more details about the API, and some other interfaces not listed in this document, please see [the full documentation](https://aegir-config.readthedocs.io/en/latest/index.html).

# Installation

The package is available on PyPI under the name [`aegir`](https://pypi.org/project/aegir/).

```
$ pip install aegir
$ poetry add aegir
$ pipenv install aegir
```

# Contributing

If you would like to join, please join [our Discord server](https://discord.akarys.me) and introduce yourself in `#aegir`. Thank you for your interest in our project!
