import logging
from pathlib import Path
from types import ModuleType
from typing import Optional

import yaml

_log = logging.getLogger(__name__)
_CONFIG_PATH = "config.yml"
_SUFFIX_KEYS = {
    "category": "categories",
    "channel": "text_channels",
    "role": "roles",
    "voice": "voice_channels",
    "webhook": "webhooks",
}


def _get_config_object(module: ModuleType) -> Optional[object]:
    """Return the config object defined in the given `module`."""
    for obj in vars(module).values():
        if isinstance(obj, type) and obj.__name__ == "Config" and obj.__module__ == module.__name__:
            return obj


def _read_config(path: str) -> dict:
    """
    Read the YAML config file at `path` and return its deserialised content.

    Raise FileNotFoundError if the file does not exist.
    """
    path = Path(path)
    if path.is_file():
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f)

    raise FileNotFoundError(f"No config found at path {path!r}")


def _load_module_config(module: ModuleType, user_config: dict) -> None:
    """
    Populate attributes of the config object in `module` with values from `user_config`.

    Raise KeyError if a configured value is not found for an attribute without a default value.
    """
    if not (obj := _get_config_object(module)):
        return

    annotations = set(obj.__annotations__)
    attributes = set(vars(obj))
    missing_defaults = annotations - attributes

    for name in attributes | annotations:
        if name.startswith("_"):
            continue  # Skip private attributes.

        # Split to get the suffix, which may determine where to find the config value.
        split_name = name.rsplit("_", 1)

        try:
            if len(split_name) > 1 and (key := _SUFFIX_KEYS.get(split_name[1])):
                # Look for the value under the corresponding guild key for the suffix.
                guild = user_config["guild"] or {}  # Avoids TypeErrors when it's None.
                category = guild[key] or {}
                new_value = category[split_name[0]]
            else:
                # All other attributes are considered specific to that extension.
                category = user_config[obj.__module__] or {}
                new_value = category[name]
        except KeyError:
            qualified = f"{obj.__module__}.{name}"
            if name in missing_defaults:
                raise KeyError(f"No config value found for {qualified} and no default specified")
            _log.debug(f"No config value found for {qualified}; keeping the default")
        else:
            _log.debug(f"Set {obj.__module__}.{name} to {new_value!r}")
            setattr(obj, name, new_value)


def load_config(bot, path: str = _CONFIG_PATH) -> None:
    """
    Populate attributes of all config objects with values from the config file at `path`.

    Raise FileNotFoundError if the config file does not exist.
    Raise KeyError if a configured value is not found for an attribute without a default value.
    """
    user_config = _read_config(path)
    for module in bot.extensions.values():
        _load_module_config(module, user_config)


def load_module_config(module: ModuleType, path: str = _CONFIG_PATH) -> None:
    """
    Populate attributes of the config object in `module` with values from the config file at `path`.

    Raise FileNotFoundError if the config file does not exist.
    Raise KeyError if a configured value is not found for an attribute without a default value.
    """
    user_config = _read_config(path)
    _load_module_config(module, user_config)
