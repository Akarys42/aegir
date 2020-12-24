"""A minimal package to support configuration files without any additional work."""

__version__ = "0.0.0-dev1"

__all__ = ("ConfigEntry", "load_config_file")

from smartconfig.configuration import ConfigEntry, load_config_file
