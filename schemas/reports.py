from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, constr
from typing import Optional

from models import district


class CategoryCreateRequest(BaseModel):
    key: str
    name: str


class ReportGenerateRequest(BaseModel):
    user_id: str
    category: str
    description: str
    kelurahan: str
    kecamatan: str
    location: str


class DescriptionRequest(BaseModel):
    user_id: str
    district: str
    village: str
    description: str = constr(min_length=12, max_length=200)
    location: str
    category: str
