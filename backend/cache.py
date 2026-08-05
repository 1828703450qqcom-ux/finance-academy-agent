"""
轻量级 TTL 内存缓存，支持30+并发
"""
import time
import threading
from typing import Any, Optional, Callable
from functools import wraps

_lock = threading.Lock()
_store: dict = {}


class TTLCache:
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 256):
        self.ttl = ttl_seconds
        self.max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        with _lock:
            entry = _store.get(key)
            if entry and time.time() < entry["expire"]:
                return entry["value"]
            if entry:
                del _store[key]
            return None

    def set(self, key: str, value: Any):
        with _lock:
            if len(_store) >= self.max_size:
                # 淘汰最早过期的
                earliest_key = min(_store, key=lambda k: _store[k]["expire"])
                del _store[earliest_key]
            _store[key] = {
                "value": value,
                "expire": time.time() + self.ttl,
            }

    def clear(self, prefix: str = ""):
        with _lock:
            keys_to_del = [k for k in _store if k.startswith(prefix)]
            for k in keys_to_del:
                del _store[k]


# 全局缓存实例
macro_cache = TTLCache(ttl_seconds=1800)   # 宏观数据缓存30分钟
stock_cache = TTLCache(ttl_seconds=300)    # 个股数据缓存5分钟
chart_cache = TTLCache(ttl_seconds=600)    # 图表数据缓存10分钟


def cached(cache: TTLCache, key_func: Callable = None):
    """装饰器：自动缓存函数返回值"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__qualname__}:{hash((args, tuple(sorted(kwargs.items()))))}"

            result = cache.get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            if result is not None:
                cache.set(cache_key, result)
            return result
        return wrapper
    return decorator
