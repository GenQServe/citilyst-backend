import logging
import os
import secrets
from urllib.parse import urlencode
import redis.asyncio as redis  # Make sure this is the async version
import requests
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException
from helpers.common import hash_password
from helpers.google_auth import GoogleAuth
from typing import List, Optional
from models.users import User
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from sqlalchemy.future import select

from schemas.users import UserCreate

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    async def get_user(self, db: AsyncSession, user_id: str) -> dict:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            user_dict = user.to_dict()
            user_dict.pop("password", None)
            return user_dict
        except Exception as e:
            logging.error(f"Error getting user: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")

    async def get_user_by_email(self, db: AsyncSession, email: str) -> dict:
        try:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            user_dict = user.to_dict()
            # user_dict.pop("password", None)
            return user_dict
        except HTTPException as e:
            logging.error(f"Error getting user by email: {str(e)}")
            raise e
        except Exception as e:
            logging.error(f"Error getting user by email: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")

    async def get_all_users(self, db: AsyncSession) -> List[dict]:
        try:
            result = await db.execute(select(User))
            users = result.scalars().all()
            users_list = [user.to_dict() for user in users]
            for user in users_list:
                user.pop("password", None)
            return users_list
        except Exception as e:
            logging.error(f"Error getting all users: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get users: {str(e)}"
            )

    # verify password
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            print(f"Verifying password: {plain_password} against {hashed_password}")
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logging.error(f"Error verifying password: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to verify password: {str(e)}"
            )

    async def create_user(self, db: AsyncSession, user_data: dict) -> dict:
        try:
            logging.info(f"Creating user with data: {user_data}")
            password = user_data.get("password")
            if password:
                hashed_password = hash_password(password)
                is_verified = False
            else:
                hashed_password = None
                is_verified = True
            utc_now = datetime.now(timezone.utc)
            image_url = user_data.get("image_url") or user_data.get("picture")
            if not image_url:
                image_url = None

            user = User(
                email=user_data.get("email"),
                password=hashed_password,
                name=user_data.get("name"),
                phone_number=user_data.get("phone_number"),
                nik=user_data.get("nik"),
                address=user_data.get("address"),
                image_url=image_url,
                role=user_data.get("role", "user"),
                is_verified=is_verified,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            user_dict = user.to_dict()
            return user_dict
        except Exception as e:
            logging.error(f"Error creating user: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to create user: {str(e)}"
            )

    async def update_user(
        self, db: AsyncSession, user_id: str, update_data: dict
    ) -> dict:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            # Update allowed fields only
            allowed_fields = [
                "email",
                "name",
                "phone_number",
                "address",
                "nik",
                "is_verified",
                "image_url",
                "password",
            ]
            for field, value in update_data.items():
                if field == "password" and value:
                    # Hash new password
                    value = pwd_context.hash(value)
                if field in allowed_fields and value is not None:
                    setattr(user, field, value)

            await db.commit()
            await db.refresh(user)
            user_dict = user.to_dict()
            user_dict.pop("password", None)
            return user_dict
        except Exception as e:
            logging.error(f"Error updating user: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to update user: {str(e)}"
            )

    async def delete_user(self, db: AsyncSession, user_id: str) -> dict:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            await db.delete(user)
            await db.commit()
            return {"message": "User deleted successfully"}
        except Exception as e:
            logging.error(f"Error deleting user: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to delete user: {str(e)}"
            )
