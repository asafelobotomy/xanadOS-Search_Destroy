#!/usr/bin/env python3
"""
Configuration management for S&D - Search & Destroy
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

# XDG Base Directory specification paths
XDG_CONFIG_HOME = os.environ.get(
    "XDG_CONFIG_HOME",
    os.path.expanduser("~/.config"))
XDG_DATA_HOME = os.environ.get(
    "XDG_DATA_HOME",
    os.path.expanduser("~/.local/share"))
XDG_CACHE_HOME = os.environ.get(
    "XDG_CACHE_HOME",
    os.path.expanduser("~/.cache"))

APP_NAME = "search-and-destroy"
CONFIG_DIR = Path(XDG_CONFIG_HOME) / APP_NAME
DATA_DIR = Path(XDG_DATA_HOME) / APP_NAME
CACHE_DIR = Path(XDG_CACHE_HOME) / APP_NAME

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = CONFIG_DIR / "config.json"
SCAN_REPORTS_DIR = DATA_DIR / "scan_reports"
QUARANTINE_DIR = DATA_DIR / "quarantine"
LOG_DIR = DATA_DIR / "logs"

# Create subdirectories
SCAN_REPORTS_DIR.mkdir(exist_ok=True)
QUARANTINE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)


def setup_logging() -> logging.Logger:
    """Setup application logging with rotation."""
    logger = logging.getLogger(APP_NAME)
    if not logger.handlers:
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler with rotation
        from logging.handlers import RotatingFileHandler

        log_file = LOG_DIR / "application.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        # Console handler for debug
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)

    return logger


def load_config(file_path: str = None) -> Dict[str, Any]:
    """Load configuration from file."""
    config_path = Path(file_path) if file_path else CONFIG_FILE
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
            # Merge with defaults to ensure all keys exist
            return {**get_default_config(), **config}
    except FileNotFoundError:
        return get_default_config()
    except json.JSONDecodeError as e:
        logging.getLogger(APP_NAME).error("Invalid JSON in config file: %s", e)
        return get_default_config()


def save_config(config_data: Dict[str, Any], file_path: str = None) -> None:
    """Save configuration to file."""
    config_path = Path(file_path) if file_path else CONFIG_FILE
    try:
        with open(config_path, "w", encoding="utf-8") as config_file:
            json.dump(config_data, config_file, indent=4, sort_keys=True)
    except (IOError, OSError) as e:
        logging.getLogger(APP_NAME).error("Failed to save config: %s", e)


def get_default_config() -> Dict[str, Any]:
    """Get default configuration values."""
    return {
        "scan_settings": {
            "scan_archives": True,
            "scan_email": True,
            "scan_ole2": True,
            "scan_pd": True,
            "scan_html": True,
            "scan_executable": True,
            "max_filesize": "100M",
            "max_recursion": 16,
            "max_files": 10000,
            "pcre_match_limit": 10000,
            "pcre_recmatch_limit": 5000,
        },
        "ui_settings": {
            "theme": "auto",  # auto, light, dark
            "show_hidden_files": False,
            "auto_update_definitions": True,
            "notifications_enabled": True,
            "minimize_to_tray": True,
            "show_scan_progress": True,
            "activity_log_retention": 100,  # Number of recent activity messages to retain
        },
        "security_settings": {
            "quarantine_enabled": True,
            "auto_quarantine_threats": False,
            "scan_removable_media": True,
            # Default: OFF - User can enable for continuous monitoring
            "real_time_protection": False,
        },
        "advanced_settings": {
            "signature_sources": ["main.cvd", "daily.cvd", "bytecode.cvd"],
            "custom_signature_urls": [],
            "log_level": "INFO",
            "scan_timeout": 300,
            "update_frequency": "daily",
        },
        "paths": {
            "quarantine_dir": str(QUARANTINE_DIR),
            "scan_reports_dir": str(SCAN_REPORTS_DIR),
            "log_dir": str(LOG_DIR),
            "temp_dir": str(CACHE_DIR / "temp"),
        },
    }
