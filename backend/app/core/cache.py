from __future__ import annotations
import os
import json
import time
import hashlib
from typing import Optional

try:
    import redis
except Exception:
    redis = None

# 进程内缓存兜底
_MEM = {}
_MEM_TTL_SEC = 6 * 60 * 60  # 6h


def _key(prefix: str, payload: str) -> str:
    h = hashlib.md5(payload.encode("utf-8")).hexdigest()
    return f"{prefix}:{h}"


class Cache:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "").strip()
        self.r = None
        if self.redis_url and redis is not None:
            try:
                self.r = redis.Redis.from_url(self.redis_url, decode_responses=True)
                self.r.ping()
            except Exception:
                self.r = None

    def get(self, key: str) -> Optional[str]:
        if self.r:
            return self.r.get(key)
        item = _MEM.get(key)
        if not item:
            return None
        value, expire_at = item
        if time.time() > expire_at:
            _MEM.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str, ttl_sec: int = _MEM_TTL_SEC) -> None:
        if self.r:
            self.r.setex(key, ttl_sec, value)
            return
        _MEM[key] = (value, time.time() + ttl_sec)


cache = Cache()


def make_summary_cache_key(text: str, mode: str) -> str:
    payload = f"{mode}\n{text}"
    return _key("summary", payload)