import gc
import os
import logging
import psutil

logger = logging.getLogger('nds_v6.memory')

_memory_limit_gb = 14.0


def set_memory_limit(gb: float):
    global _memory_limit_gb
    _memory_limit_gb = gb
    logger.info(f"内存上限设置为 {gb:.1f} GB")


def get_memory_mb() -> float:
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def get_memory_gb() -> float:
    return get_memory_mb() / 1024


def check_memory() -> bool:
    current = get_memory_gb()
    if current > _memory_limit_gb:
        return False
    return True


def force_gc():
    collected = gc.collect()
    after = get_memory_mb()
    logger.debug(f"GC 回收 {collected} 个对象, 当前内存 {after:.1f} MB")
    return collected


def check_and_gc() -> bool:
    current_gb = get_memory_gb()
    if current_gb > _memory_limit_gb:
        logger.warning(f"内存 {current_gb:.1f} GB 超过上限 {_memory_limit_gb:.1f} GB, 执行 GC")
        force_gc()
        current_gb = get_memory_gb()
        if current_gb > _memory_limit_gb:
            logger.error(f"GC 后内存仍为 {current_gb:.1f} GB, 超过上限")
            return False
    return True


def get_status() -> dict:
    current_mb = get_memory_mb()
    return {
        'current_mb': round(current_mb, 1),
        'current_gb': round(current_mb / 1024, 2),
        'limit_gb': _memory_limit_gb,
        'usage_percent': round(current_mb / (_memory_limit_gb * 1024) * 100, 1),
        'is_over_limit': current_mb > _memory_limit_gb * 1024,
    }
