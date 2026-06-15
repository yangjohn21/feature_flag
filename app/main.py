from fastapi import FastAPI

from app.api.v1 import feature
from app.core.config import config
from app.core.logging import setup_logging
from app.db.schema import Base, engine

setup_logging()
Base.metadata.create_all(bind=engine)

app = FastAPI(title=config.app_name)


@app.get("/health")
def health():
    return {"status": "ok"}


# Register routes
app.include_router(feature.router, prefix="/api/v1")
