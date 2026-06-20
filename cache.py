import os
import json
from upstash_redis import Redis
from dotenv import load_dotenv

load_dotenv()

_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(
            url=os.getenv("UPSTASH_REDIS_REST_URL"),
            token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
        )
    return _redis_client


def cache_get(key: str):
    try:
        r = get_redis()
        value = r.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception:
        return None


def cache_set(key: str, value, ttl_seconds: int = 3600):
    try:
        r = get_redis()
        r.set(key, json.dumps(value), ex=ttl_seconds)
    except Exception:
        pass


def cache_clear_all():
    try:
        r = get_redis()
        r.flushall()
    except Exception:
        pass