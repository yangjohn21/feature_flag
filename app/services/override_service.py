from typing import Optional

from sqlalchemy.orm import Session

from app.db.schema import FeatureFlag, FeatureFlagOverride
from app.services.cache import TTLCache


class OverrideService:
    def __init__(self, session: Session, cache: TTLCache | None = None):
        self._db = session
        self._cache = cache

    def set_user_override(self, name: str, user_id: int, enabled: bool) -> Optional[FeatureFlagOverride]:
        # find flag
        flag = self._db.query(FeatureFlag).filter(FeatureFlag.name == name).first()
        if not flag:
            return None

        override = (
            self._db.query(FeatureFlagOverride)
            .filter(FeatureFlagOverride.flag_id == flag.id)
            .filter(FeatureFlagOverride.user_id == user_id)
            .first()
        )
        if override:
            override.enabled = enabled
        else:
            override = FeatureFlagOverride(flag_id=flag.id, user_id=user_id, enabled=enabled)
            self._db.add(override)

        self._db.commit()

        # invalidate evaluation cache for this user/flag
        if self._cache:
            self._cache.delete(f"eval:{name}:{user_id}")

        return override

    def get_user_override(self, name: str, user_id: int) -> Optional[FeatureFlagOverride]:
        flag = self._db.query(FeatureFlag).filter(FeatureFlag.name == name).first()
        if not flag:
            return None
        override = (
            self._db.query(FeatureFlagOverride)
            .filter(FeatureFlagOverride.flag_id == flag.id)
            .filter(FeatureFlagOverride.user_id == user_id)
            .first()
        )
        return override
