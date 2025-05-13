from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone
import cuid
from sqlalchemy import (
    JSON,
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
from helpers.db import Base


def generate_cuid():
    """Fungsi untuk menghasilkan CUID"""
    return cuid.cuid()


class User(Base):
    __tablename__ = "tbl_users"

    id = Column(String(25), primary_key=True, default=generate_cuid)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    image_url = Column(String(255), nullable=True)
    role = Column(String(50), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __init__(self, email: str, **kwargs):
        self.email = email
        self.id = generate_cuid()
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.last_login = kwargs.get("last_login")
        self.role = kwargs.get("role", "user")
        self.password = kwargs.get("password")
        self.image_url = kwargs.get("image_url")
        self.name = kwargs.get("name")
        self.phone_number = kwargs.get("phone_number")
        self.address = kwargs.get("address")
        self.date_of_birth = kwargs.get("date_of_birth")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "password": self.password,
            "name": self.name,
            "phone_number": self.phone_number,
            "address": self.address,
            "date_of_birth": self.date_of_birth,
            "image_url": self.image_url,
            "role": self.role,
            "last_login": self.last_login,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
