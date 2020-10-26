import logging
from pathlib import Path

import yaml

_log = logging.getLogger(__name__)
_CONFIG: dict = {}


def read_config(path: str = "config.yml") -> None:
    """
    Read the YAML config file at `path` and store the contents internally.

    Raise FileNotFoundError if the file does not exist.
    """
    global _CONFIG
    path = Path(path)

    if path.is_file():
        with path.open(encoding="utf-8") as f:
            _CONFIG = yaml.safe_load(f)

    raise FileNotFoundError(f"No config found at path {path!r}")
