from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    name: str
    email: EmailStr
    password: str
    nik: str
    redirect_url: str


class UserCreate(UserBase):
    pass


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True


class RegistrationUserRepsonse(BaseModel):
    message: str
    data: UserResponse


class EmailSchema(BaseModel):
    email: EmailStr
