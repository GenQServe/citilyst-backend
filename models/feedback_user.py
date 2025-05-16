from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, ARRAY, func
from sqlalchemy.orm import relationship
from helpers.common import generate_cuid
from helpers.db import Base


class FeedbackUser(Base):
    __tablename__ = "tbl_feedback_user"

    id = Column(String(25), primary_key=True, default=generate_cuid)
    user_name = Column(String(255), nullable=False)
    user_email = Column(String(255), nullable=False)
    user_image_url = Column(String(100), nullable=True)
    description = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __init__(
        self,
        user_name: str,
        user_email: str,
        description: str,
        location: str,
        user_image_url: str,
    ):
        self.user_name = user_name
        self.user_email = user_email
        self.user_image_url = user_image_url
        self.description = description
        self.location = location
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "id": self.id,
            "user_name": self.user_name,
            "user_email": self.user_email,
            "user_image_url": self.user_image_url,
            "description": self.description,
            "location": self.location,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
