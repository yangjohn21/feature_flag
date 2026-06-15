from fastapi import FastAPI

from app.api.v1 import feature
from app.core.config import config
from app.core.logging import setup_logging
from app.db.schema import Base, engine
import re
import logging

setup_logging()

# Log the resolved DB URL with the password masked to help debugging environment issues
def _mask_db_url(url: str) -> str:
    return re.sub(r"(://[^:/]+:)([^@]+)(@)", r"\1***\3", url)

logger = logging.getLogger()
logger.info("Resolved DB URL: %s", _mask_db_url(config.db_url))

Base.metadata.create_all(bind=engine)

app = FastAPI(title=config.app_name)


@app.get("/health")
def health():
    return {"status": "ok"}


# Register routes
app.include_router(feature.router, prefix="/api/v1")
