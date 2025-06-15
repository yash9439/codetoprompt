"""Configuration management for CodeToPrompt."""

import toml
from pathlib import Path
from typing import Dict, Any, List, Optional

APP_NAME = "codetoprompt"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.toml"

# Sensible defaults for a new user.
DEFAULT_CONFIG = {
    "show_line_numbers": False,
    "compress": False,
    "respect_gitignore": True,
    "count_tokens": True,
    "max_tokens": None,
    "include_patterns": [],
    "exclude_patterns": [],
    "tree_depth": 5,
    "output_format": "default",
}

def get_config_path() -> Path:
    """Returns the path to the config file."""
    return CONFIG_FILE

def load_config() -> Dict[str, Any]:
    """Loads configuration from the file, merging with defaults."""
    config_path = get_config_path()
    config = DEFAULT_CONFIG.copy()
    if config_path.is_file():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = toml.load(f)
            # A 'settings' table inside the toml file
            if "settings" in user_config and isinstance(user_config["settings"], dict):
                config.update(user_config["settings"])
        except Exception:
            # Fallback to defaults if config is invalid
            pass
    return config

def save_config(config: Dict[str, Any]):
    """Saves the configuration to the file."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        toml.dump({"settings": config}, f)

def reset_config() -> bool:
    """Deletes the configuration file, resetting to defaults.
    
    Returns True if the file existed and was deleted, False otherwise.
    """
    config_path = get_config_path()
    if config_path.is_file():
        config_path.unlink()
        return True
    return False