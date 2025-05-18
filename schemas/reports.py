from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class ReportGenerateRequest(BaseModel):
    user_id: str
    category: str
    description: str
    kelurahan: str
    kecamatan: str
    location: str
