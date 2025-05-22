from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, constr
from typing import Optional

from models import district


class CategoryCreateRequest(BaseModel):
    key: str
    name: str


class ReportGenerateRequest(BaseModel):
    report_id: str
    user_id: str
    category_key: str
    formal_description: str
    district_id: str
    village_id: str
    location: str
    file_url: Optional[str] = None
    images_url: list[str]


class DescriptionRequest(BaseModel):
    report_id: Optional[str] = None
    user_id: str
    category_key: str
    district_id: str
    village_id: str
    description: str = constr(min_length=12, max_length=200, to_lower=True)
    location: str
