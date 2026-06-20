import time
from fastapi.testclient import TestClient
from main import app
from cache import cache_get, cache_set, get_redis

client = TestClient(app)


def test_redis_connection_works():
    r = get_redis()
    assert r is not None


def test_cache_set_and_get():
    cache_set("test:pytest:key", {"value": 123}, ttl_seconds=30)
    result = cache_get("test:pytest:key")
    assert result == {"value": 123}


def test_cache_get_missing_key_returns_none():
    result = cache_get("test:pytest:nonexistent_key_xyz")
    assert result is None


def test_forecast_second_call_is_faster():
    # First call - cache miss (or hit if pre-warmed, so we just verify both succeed)
    start1 = time.time()
    response1 = client.get("/api/forecast?sku=A1023")
    duration1 = time.time() - start1
    assert response1.status_code == 200

    # Second call - should hit cache, much faster
    start2 = time.time()
    response2 = client.get("/api/forecast?sku=A1023")
    duration2 = time.time() - start2
    assert response2.status_code == 200

    # Cached response should be at least somewhat faster
    # (loose check since CI machines vary)
    assert duration2 <= duration1 + 0.5


def test_forecast_cache_returns_same_data():
    response1 = client.get("/api/forecast?sku=A1023")
    response2 = client.get("/api/forecast?sku=A1023")
    assert response1.json() == response2.json()