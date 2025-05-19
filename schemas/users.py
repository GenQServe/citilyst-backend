from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional
from fastapi import UploadFile, File


class UserBase(BaseModel):
    name: str
    email: EmailStr
    password: str
    nik: str
    # redirect_url: str


class UserCreate(UserBase):
    pass


class UserCreateByAdmin(BaseModel):
    name: str
    email: EmailStr
    password: str
    nik: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    nik: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:

        from_attributes = True


class RegistrationUserRepsonse(BaseModel):
    message: str
    data: UserResponse


class EmailSchema(BaseModel):
    email: EmailStr
