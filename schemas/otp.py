# tolong buatkan schema otp
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class OTPRequest(BaseModel):
    email: EmailStr
    otp: str


class OTPResponse(BaseModel):
    message: str
    data: Optional[dict] = None
    status: bool


class OTPResendRequest(BaseModel):
    email: EmailStr
