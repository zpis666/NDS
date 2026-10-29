import sys
from loguru import logger
from config import BASE_DIR, get_runtime_config


def setup_logger():
    config = get_runtime_config()
    log_level = config.get('log_level', 'INFO')
    log_dir = BASE_DIR / "output"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()

    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    logger.add(
        str(log_dir / "nds_v6.log"),
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        mode='w'
    )

    return logger
