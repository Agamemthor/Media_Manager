#!/usr/bin/env python3
"""
Media Manager – entry point.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def load_json_config(path: Path) -> Dict[str, Any]:
    """Load a JSON config file."""
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Config file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON: {path}") from exc


def load_env_vars(*keys: str, defaults: Dict[str, str] | None = None) -> Dict[str, Any]:
    """Get environment variables, raising if mandatory are missing."""
    defaults = defaults or {}
    env: Dict[str, Any] = {}
    for key in keys:
        val = os.getenv(key, defaults.get(key))
        if val is None:
            raise RuntimeError(f"Missing env var: {key}")
        env[key] = val
    return env


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")
CONFIG_PATH = BASE_DIR / "configs" / "appconfig_1t1cs.json"
APP_CONFIG: Dict[str, Any] = load_json_config(CONFIG_PATH)

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# GUI Application
# ------------------------------------------------------------
class MediaManagerApp:
    """Wraps MediaManager and starts the Tk loop."""

    def __init__(self) -> None:
        db_env_keys = (
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD",
            "DB_HOST",
            "DB_PORT",
            "DB_RETRIES",
            "DB_DELAY",
        )
        db_env = load_env_vars(*db_env_keys)

        self.conn_config: Dict[str, Any] = {
            "dbname": db_env["DB_NAME"],
            "user": db_env["DB_USER"],
            "password": db_env["DB_PASSWORD"],
            "host": db_env["DB_HOST"],
            "port": int(db_env["DB_PORT"]),
            "retries": int(db_env["DB_RETRIES"]),
            "delay": int(db_env["DB_DELAY"]),
        }

        window_cfg = APP_CONFIG.get("window", {})
        window_manager_cfg = APP_CONFIG.get("window_manager", {})
        custom_grid_cfg = APP_CONFIG.get("custom_grid", {})

        from classes import MediaManager  # lazy import

        self.media_manager = MediaManager(
            conn_config=self.conn_config,
            window_config=window_cfg,
            grid_config=custom_grid_cfg,
            window_manager_config=window_manager_cfg,
        )

# ------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------
def main() -> None:
    """Run the application."""
    try:
        app = MediaManagerApp()
        app.media_manager.root.mainloop()
    except Exception:
        logger.exception("Failed to start application")

if __name__ == "__main__":
    main()