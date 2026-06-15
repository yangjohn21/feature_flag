from sqlalchemy import String, create_engine, event
import os
import re
import logging
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.core.config import config

# Allow enabling SQL echo for debugging via env var SQL_ECHO=true
echo = os.getenv("SQL_ECHO", "false").lower() in ("1", "true", "yes")

# Pass an application_name so Postgres logs show which connections belong to this app
connect_args = {"application_name": config.app_name}

engine = create_engine(config.db_url, echo=echo, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Log the masked DB URL for each executed query so we can identify which DB handled it.
_engine_logger = logging.getLogger("sqlalchemy.engine.Engine")

def _mask_db_url(url: str) -> str:
    try:
        return re.sub(r"(://[^:/]+:)([^@]+)(@)", r"\1***\3", url)
    except Exception:
        return "<masked>"


@event.listens_for(engine, "before_cursor_execute")
def _log_db_url_before_execute(conn, cursor, statement, parameters, context, executemany):
    try:
        url = str(conn.engine.url)
    except Exception:
        url = config.db_url
    _engine_logger.info("DB URL for query: %s", _mask_db_url(url))


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
