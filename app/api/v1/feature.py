from fastapi import APIRouter, Depends, HTTPException, status

from app.db.schema import SessionLocal
from app.models.feature import (
    FeatureCreate,
    FeatureRead,
    FeatureUpdateState,
    EvalResponse,
)
from app.services.flag_service import FlagService
from app.services.cache import cache as shared_cache
from app.services.override_service import OverrideService

router = APIRouter()


def get_flag_service():
    session = SessionLocal()
    try:
        # single shared in-memory cache per request dependency instance
        # reuse process-global cache so GETs are cached across requests
        yield FlagService(session=session, cache=shared_cache)
    finally:
        session.close()


@router.post("/flags", response_model=FeatureRead, status_code=status.HTTP_201_CREATED)
def create_flag(payload: FeatureCreate, service: FlagService = Depends(get_flag_service)):
    existing = service.get_flag(payload.name)
    if existing:
        raise HTTPException(status_code=409, detail="Feature already exists")
    flag = service.create_flag(payload.name, payload.description, payload.default_enabled)
    return flag


@router.get("/flags", response_model=list[FeatureRead])
def list_flags(service: FlagService = Depends(get_flag_service)):
    return service.list_flags()


@router.put("/flags/{name}/global", response_model=FeatureRead)
def set_global(name: str, payload: FeatureUpdateState, service: FlagService = Depends(get_flag_service)):
    flag = service.set_global(name, payload.enabled)
    if not flag:
        raise HTTPException(status_code=404, detail="Feature not found")
    return flag


@router.put("/flags/{name}/users/{user_id}", status_code=status.HTTP_200_OK)
def set_user_override(name: str, user_id: int, payload: FeatureUpdateState, service: FlagService = Depends(get_flag_service)):
    # use OverrideService for per-user override operations
    session = service._db
    override_service = OverrideService(session=session, cache=service._cache)
    ov = override_service.set_user_override(name, user_id, payload.enabled)
    if not ov:
        raise HTTPException(status_code=404, detail="Feature not found")
    return {"success": True}


@router.get("/flags/{name}/evaluate", response_model=EvalResponse)
def evaluate(name: str, user_id: int | None = None, service: FlagService = Depends(get_flag_service)):
    try:
        enabled = service.evaluate(name, user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Feature not found")
    return EvalResponse(feature=name, user_id=user_id, enabled=enabled)
