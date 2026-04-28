import sys
import os
import yaml
from pathlib import Path


def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


BASE_DIR = _get_base_dir()
CONFIG_PATH = BASE_DIR / "config.yaml"

_config = None


def load_config(config_path=None):
    global _config
    if _config is not None and config_path is None:
        return _config

    path = config_path or CONFIG_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"配置文件不存在: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        _config = yaml.safe_load(f)

    return _config


def get_db_config(db_type):
    config = load_config()
    return config['databases'][db_type]


def get_mysql_databases():
    config = load_config()
    return config['databases']['mysql']['databases']


def get_postgresql_databases():
    config = load_config()
    return config['databases']['postgresql']['databases']


def get_sensitive_level(sensitive_type):
    config = load_config()
    levels = config.get('sensitive_levels', {})
    for level, types in levels.items():
        if sensitive_type in types:
            return level
    return 'L1'


def get_output_path():
    config = load_config()
    return BASE_DIR / config['output']['csv_path']


def get_runtime_config():
    config = load_config()
    return config.get('runtime', {})


def get_ocr_config():
    config = load_config()
    return config.get('ocr', {})
