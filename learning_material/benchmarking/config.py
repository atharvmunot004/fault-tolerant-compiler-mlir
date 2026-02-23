"""
Load and validate benchmark configuration from llm.json.
"""

import json
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).parent / "llm.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load benchmark configuration from JSON file."""
    p = path or CONFIG_PATH
    with open(p, encoding="utf-8") as f:
        return json.load(f)
