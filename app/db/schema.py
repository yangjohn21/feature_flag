from sqlalchemy import String, create_engine
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.core.config import config

engine = create_engine(config.db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    default_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    # If global_enabled is None, fall back to default_enabled
    global_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class FeatureFlagOverride(Base):
    __tablename__ = "feature_flag_overrides"

    id: Mapped[int] = mapped_column(primary_key=True)
    flag_id: Mapped[int] = mapped_column(Integer, ForeignKey("feature_flags.id"), index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
