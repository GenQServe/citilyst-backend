from datetime import datetime
from pydantic import BaseModel, EmailStr


class BasicAuthRequest(BaseModel):
    email: EmailStr
    password: str
