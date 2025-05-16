from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class FeedbackUserRequest(BaseModel):
    user_name: str
    user_email: EmailStr
    user_image_url: Optional[str] = None
    description: str
    location: Optional[str] = None
