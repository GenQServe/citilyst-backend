from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class DistrictCreate(BaseModel):
    name: str


class DistrictUpdate(BaseModel):
    name: Optional[str] = None


class DistrictResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class DistrictListResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class VillageCreate(BaseModel):
    name: str
    district_id: str


class VillageUpdate(BaseModel):
    name: Optional[str] = None
    district_id: Optional[str] = None


class VillageResponse(BaseModel):
    id: str
    name: str
    district_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class VillageListResponse(BaseModel):
    id: str
    name: str
    district_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
