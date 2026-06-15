from pydantic import BaseModel
from typing import Optional


class FeatureCreate(BaseModel):
    name: str
    description: Optional[str] = None
    default_enabled: bool = False


class FeatureRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    default_enabled: bool
    global_enabled: Optional[bool]


class FeatureUpdateState(BaseModel):
    enabled: bool


class EvalResponse(BaseModel):
    feature: str
    user_id: Optional[int]
    enabled: bool
