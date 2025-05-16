from datetime import datetime, timedelta, timezone
import logging
import os
from fastapi import HTTPException
from jose import JWTError, jwt
from helpers.config import settings


class JwtHelper:
    JWT_SECRET = settings.JWT_SECRET

    def __init__(self):
        self.secret_key = self.JWT_SECRET
        if not self.secret_key:
            raise ValueError("JWT_SECRET environment variable is not set")

    def encode(self, payload: dict) -> str:
        return jwt.encode(payload, self.secret_key or "", algorithm="HS256")

    def decode(self, token: str) -> dict:
        return jwt.decode(token, self.secret_key or "", algorithms=["HS256"])

    def create_token(self, user_data: dict) -> str:
        """
        Create JWT token with user data
        """
        try:
            logging.info(f"Creating token for user: {user_data}")
            payload = {
                "sub": user_data.get("id"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                # "picture": user_data.get("picture"),
                # "phone": user_data.get("phone"),
                # "address": user_data.get("address"),
                "is_verified": user_data.get("is_verified"),
                "role": user_data.get("role"),
                "exp": datetime.now(timezone.utc) + timedelta(days=1),
            }
            access_token = self.encode(payload)
            return access_token
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to create token: {str(e)}"
            )

    def create_refresh_token(self, user_data: dict) -> str:
        """
        Create JWT refresh token with user data
        """
        try:
            payload = {
                "sub": user_data.get("id"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "picture": user_data.get("picture"),
                "phone": user_data.get("phone"),
                "address": user_data.get("address"),
                "exp": datetime.now(timezone.utc) + timedelta(days=30),
            }
            refresh_token = self.encode(payload)
            return refresh_token
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to create refresh token: {str(e)}"
            )
