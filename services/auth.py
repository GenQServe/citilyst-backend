import logging
import os
import secrets
from urllib.parse import urlencode
import redis.asyncio as redis  # Make sure this is the async version
import requests
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException, Request
from helpers.google_auth import GoogleAuth
from typing import Optional
from models.users import User
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from sqlalchemy.future import select

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    async def login_google(
        self, redirect_uri: str, path: str, request: Request = None
    ) -> dict:
        """
        Login with Google OAuth2.0
        """
        try:
            request_scheme = "http" if request.url.hostname == "localhost" else "https"
            google_redirect_uri = GoogleAuth.get_redirect_uri(request)
            print(f"Google Redirect URI: {google_redirect_uri}")
            state_token = secrets.token_urlsafe(16)
            await redis_client.setex(f"redirect_uri:{state_token}", 3600, redirect_uri)
            await redis_client.setex(f"path:{state_token}", 3600, path)

            google_auth_url = "https://accounts.google.com/o/oauth2/auth?" + urlencode(
                {
                    "client_id": GoogleAuth.get_client_id(),
                    "redirect_uri": google_redirect_uri,
                    "response_type": "code",
                    "scope": "openid email profile",
                    "state": state_token,
                    "access_type": "offline",
                }
            )
            return {"url": google_auth_url}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to login with Google: {str(e)}"
            )

    async def authenticate_with_google(
        self, code: str, request: Request = None
    ) -> dict:
        """
        Authenticate user with Google OAuth2.0
        """
        try:
            token_url = "https://accounts.google.com/o/oauth2/token"

            data = {
                "code": code,
                "client_id": GoogleAuth.get_client_id(),
                "client_secret": GoogleAuth.get_client_secret(),
                "redirect_uri": GoogleAuth.get_redirect_uri(request),
                "grant_type": "authorization_code",
            }
            response = requests.post(token_url, data=data)

            if not response.ok:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Google authentication failed: {response.text}",
                )

            access_token = response.json().get("access_token")

            if not access_token:
                raise HTTPException(
                    status_code=400, detail="Failed to obtain access token"
                )

            user_info_response = requests.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if not user_info_response.ok:
                raise HTTPException(
                    status_code=user_info_response.status_code,
                    detail=f"Failed to get user info: {user_info_response.text}",
                )

            return user_info_response.json()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Authentication error: {str(e)}"
            )

    def create_token(self, user_data: dict) -> str:
        """
        Create JWT token with user data
        """
        try:
            payload_1 = {
                "sub": user_data.get("id"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "picture": user_data.get("picture"),
                "phone": user_data.get("phone"),
                "address": user_data.get("address"),
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            }
            access_token = jwt.encode(
                payload_1, GoogleAuth.get_client_secret(), algorithm="HS256"
            )
            payload_2 = {
                "sub": user_data.get("id"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "picture": user_data.get("picture"),
                "phone": user_data.get("phone"),
                "address": user_data.get("address"),
                "exp": datetime.now(timezone.utc) + timedelta(days=30),
            }
            refresh_token = jwt.encode(
                payload_2, GoogleAuth.get_client_secret(), algorithm="HS256"
            )
            return access_token

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to create token: {str(e)}"
            )
