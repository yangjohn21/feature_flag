from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
import os

from app.db.schema import FeatureFlag
from app.services.cache import TTLCache
from app.services.override_service import OverrideService


class FlagService:
    def __init__(self, session: Session, cache: Optional[TTLCache] = None):
        self._db = session
        self._cache = cache or TTLCache()

    def create_flag(self, name: str, description: Optional[str], default_enabled: bool) -> FeatureFlag:
        flag = FeatureFlag(name=name, description=description, default_enabled=default_enabled)
        self._db.add(flag)
        self._db.commit()
        self._db.refresh(flag)
        # cache flag
        flag_ttl = int(os.getenv("FLAG_CACHE_TTL", "300"))
        self._cache.set(f"flag:{flag.name}", flag, ttl=flag_ttl)
        return flag

    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        cached = self._cache.get(f"flag:{name}")
        if cached:
            return cached
        stmt = select(FeatureFlag).where(FeatureFlag.name == name)
        flag = self._db.execute(stmt).scalars().first()
        if flag:
            flag_ttl = int(os.getenv("FLAG_CACHE_TTL", "300"))
            self._cache.set(f"flag:{name}", flag, ttl=flag_ttl)
        return flag

    def list_flags(self) -> list[FeatureFlag]:
        stmt = select(FeatureFlag)
        return self._db.execute(stmt).scalars().all()

    def set_global(self, name: str, enabled: bool) -> Optional[FeatureFlag]:
        flag = self.get_flag(name)
        if not flag:
            return None
        flag.global_enabled = enabled
        self._db.commit()
        self._cache.delete(f"flag:{name}")
        # invalidate any cached evaluations for this flag
        self._cache.delete_prefix(f"eval:{name}:")
        return flag

    # Per-user overrides are handled by OverrideService

    def evaluate(self, name: str, user_id: Optional[int] = None) -> bool:
        key = f"eval:{name}:{user_id or 'anon'}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        flag = self.get_flag(name)
        if not flag:
            raise ValueError("Feature not found")

        # user override should take precedence over global
        if user_id is not None:
            override_service = OverrideService(session=self._db, cache=self._cache)
            override = override_service.get_user_override(name, user_id)
            if override:
                result = bool(override.enabled)
                eval_ttl = int(os.getenv("EVAL_CACHE_TTL", "60"))
                self._cache.set(key, result, ttl=eval_ttl)
                return result

        # global override
        if flag.global_enabled is not None:
            result = bool(flag.global_enabled)
            eval_ttl = int(os.getenv("EVAL_CACHE_TTL", "60"))
            self._cache.set(key, result, ttl=eval_ttl)
            return result

        # default
        result = bool(flag.default_enabled)
        eval_ttl = int(os.getenv("EVAL_CACHE_TTL", "60"))
        self._cache.set(key, result, ttl=eval_ttl)
        return result
