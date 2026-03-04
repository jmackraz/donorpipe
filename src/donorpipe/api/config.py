"""App configuration loaded from config.json."""

import json
import os
from pathlib import Path

from pydantic import BaseModel


class AccountConfig(BaseModel):
    data_base: str
    data_dirs: list[str]


class AppConfig(BaseModel):
    accounts: dict[str, AccountConfig]


def load_config(path: Path | None = None) -> AppConfig:
    if path is None:
        config_path = os.environ.get("DONORPIPE_CONFIG", "config.json")
        path = Path(config_path)
    with open(path) as f:
        return AppConfig.model_validate(json.load(f))
