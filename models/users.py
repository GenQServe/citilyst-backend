from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone
import cuid
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    func,
    select,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from helpers.common import generate_cuid
from helpers.db import Base


class User(Base):
    __tablename__ = "tbl_users"

    id = Column(String(25), primary_key=True, default=generate_cuid)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    nik = Column(String(50), nullable=True)
    phone_number = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)
    role = Column(String(50), nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __init__(self, email: str, **kwargs):
        self.email = email
        self.id = generate_cuid()
        self.role = kwargs.get("role", "user")
        self.password = kwargs.get("password")
        self.image_url = kwargs.get("image_url")
        self.name = kwargs.get("name")
        self.nik = kwargs.get("nik")
        self.phone_number = kwargs.get("phone_number")
        self.address = kwargs.get("address")
        self.is_verified = kwargs.get("is_verified", False)
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "nik": self.nik,
            "phone_number": self.phone_number,
            "address": self.address,
            "image_url": self.image_url,
            "role": self.role,
            "is_verified": self.is_verified,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
