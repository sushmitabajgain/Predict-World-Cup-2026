from collections.abc import Generator

from sqlalchemy.orm import Session

from app.database import get_db
from app.services.cache import CacheService


def get_session() -> Generator[Session, None, None]:
    yield from get_db()


def get_cache() -> CacheService:
    return CacheService()
