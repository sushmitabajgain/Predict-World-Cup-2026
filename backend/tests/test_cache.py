from app.services.cache import CacheService


class MockRedis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def setex(self, key, ttl, value):
        self.values[key] = value


def test_redis_cache_with_mocked_client():
    service = CacheService(client=MockRedis())
    service.set_json("example", {"value": 7})
    assert service.get_json("example") == {"value": 7}
