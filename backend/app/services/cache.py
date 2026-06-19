import json
from collections.abc import Callable
from typing import Any

import redis

from app.config import get_settings


class CacheService:
    def __init__(self, client: redis.Redis | None = None) -> None:
        settings = get_settings()
        self.client = client or redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def get_json(self, key: str) -> Any | None:
        try:
            raw = self.client.get(key)
        except redis.RedisError:
            return None
        if raw is None:
            return None
        return json.loads(raw)

    def set_json(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        try:
            self.client.setex(key, ttl_seconds, json.dumps(value, default=str))
        except redis.RedisError:
            return

    def get_or_set(self, key: str, factory: Callable[[], Any], ttl_seconds: int = 3600) -> Any:
        cached = self.get_json(key)
        if cached is not None:
            return cached
        value = factory()
        self.set_json(key, value, ttl_seconds)
        return value


def teams_key() -> str:
    return "teams:world-cup-2026:v1"


def prediction_key(team_a: str, team_b: str, match_date: str) -> str:
    return f"prediction:{team_a.lower()}:{team_b.lower()}:{match_date}"


def features_key(team_a: str, team_b: str, match_date: str) -> str:
    return f"features:{team_a.lower()}:{team_b.lower()}:{match_date}"


def worldcup_cache_key(resource: str, *parts: object) -> str:
    suffix = ":".join(str(part).lower().replace(" ", "-") for part in parts if part is not None and part != "")
    return f"worldcup:api-football:{resource}{':' + suffix if suffix else ''}:v1"
