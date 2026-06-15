from fastapi import FastAPI

from app.api.v1 import feature
from app.core.config import config
from app.core.logging import setup_logging
from app.db.schema import Base, engine
import logging
import os
from contextlib import asynccontextmanager

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        logging.getLogger(__name__).warning("Skipping DB create_all at startup: %s", exc)
    yield

app = FastAPI(title=config.app_name, lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


# Register routes
app.include_router(feature.router, prefix="/api/v1")
