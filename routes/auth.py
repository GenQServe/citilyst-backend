import logging
import os
import sys
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.params import Cookie, Header
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from helpers.google_auth import GoogleAuth
from sqlalchemy.ext.asyncio import AsyncSession
from helpers.db import db_connection, get_db
from services.auth import AuthService
import redis.asyncio as redis

from services.users import UserService

is_production = (
    os.getenv("ENVIRONMENT", "development").lower() == "production"
    or "--production" in sys.argv
)

routes_auth = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


# buatkan route untuk login dengan email dan password
@routes_auth.post(
    "/login",
    summary="Login with Email and Password",
    description="Login with email and password",
)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService()
    user_service = UserService()
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    print(f"Data: {data}")
    if not email or not password:
        return JSONResponse(
            status_code=400,
            content={"message": "Email and password are required"},
        )
    try:
        user = await user_service.get_user_by_email(db, email)
        print(f"User: {user}")
        if not user:
            raise HTTPException(status_code=401, detail="Email not registered")

        if not user["password"]:
            raise HTTPException(status_code=401, detail="Email not registered")

        if not user_service.verify_password(password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid password")

        token = auth_service.create_token(user)
        return JSONResponse(
            status_code=201,
            content={
                "message": "Login successful",
                "data": {
                    "token": token,
                    "user": {
                        "id": user["id"],
                        "email": user["email"],
                        "name": user["name"],
                        "image_url": user["image_url"],
                    },
                },
            },
        )
    except HTTPException as e:
        logging.error(f"Login error: {e.status_code}: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={"message": str(e.detail)},
        )
    except Exception as e:
        print(f"Login error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"},
        )


@routes_auth.get(
    "/google",
    summary="Login with Google",
    description="Login with Google OAuth2.0",
)
async def login_google(
    redirect_uri: str, path: Optional[str] = None, request: Request = None
):
    auth_service = AuthService()
    result = await auth_service.login_google(redirect_uri, path, request)
    return result


@routes_auth.get("/google/callback")
async def auth_google(
    code: str,
    state: str,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        auth_service = AuthService()
        user_service = UserService()
        logging.info(f"Authenticating with Google code: {code}")
        logging.info(f"Authenticating with Google state: {state}")

        redirect_uri = await redis_client.get(f"redirect_uri:{state}")
        if not redirect_uri:
            raise HTTPException(
                status_code=400, detail="Invalid or expired state token"
            )

        path = await redis_client.get(f"path:{state}")
        user_info = await auth_service.authenticate_with_google(code, request)
        if not user_info:
            raise HTTPException(
                status_code=400, detail="Failed to authenticate with Google"
            )
        print(f"User info: {user_info}")

        existing_user = None
        try:
            existing_user = await user_service.get_user_by_email(db, user_info["email"])
        except HTTPException as e:
            if e.status_code != 404:
                raise
            print(f"User not found: {user_info['email']}")
            existing_user = None

        if existing_user:
            logging.info(f"Updating existing user: {user_info['email']}")
            update_data = {
                "name": user_info.get("name"),
                "image_url": user_info.get(
                    "picture"
                ),  # Gunakan image_url, bukan picture
                "email": user_info.get("email"),
            }
            updated_user = await user_service.update_user(
                db, existing_user["id"], update_data
            )
            user_info["id"] = updated_user["id"]
            user_info["name"] = updated_user["name"]
            user_info["picture"] = updated_user[
                "image_url"
            ]  # Mapping kembali ke picture untuk token
        else:
            logging.info(f"Creating new user: {user_info['email']}")
            create_data = {
                "email": user_info["email"],
                "name": user_info.get("name"),
                "image_url": user_info.get("picture"),  # Gunakan image_url di DB
                # Tidak perlu password untuk OAuth user
            }
            created_user = await user_service.create_user(db, create_data)
            user_info["id"] = created_user["id"]
            user_info["name"] = created_user["name"]
            user_info["picture"] = created_user[
                "image_url"
            ]  # Mapping kembali ke picture untuk token

        token = auth_service.create_token(user_info)
        frontend_url = redirect_uri

        if path:
            if not frontend_url.endswith("/") and not path.startswith("/"):
                frontend_url += "/"
            elif frontend_url.endswith("/") and path.startswith("/"):
                path = path[1:]

            frontend_url += path
        redirect_response = RedirectResponse(url=frontend_url)

        redirect_response.set_cookie(
            key="token",
            value=token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=86400,
            path="/",
        )
        await redis_client.delete(f"redirect_uri:{state}")
        if path:
            await redis_client.delete(f"path:{state}")

        return redirect_response
    except HTTPException as e:
        logging.error(f"Auth error: {e.status_code}: {e.detail}")
        error_url = f"{redirect_uri}?auth/login?status=error"
        return RedirectResponse(url=error_url)
    except Exception as e:
        logging.error(f"Auth error: {str(e)}")
        error_url = f"{redirect_uri}?auth/login?status=error"
        return RedirectResponse(url=error_url)


@routes_auth.get(
    "/token",
    summary="Get Token",
    description="Get user info from token in cookie or Authorization header",
)
async def get_token(
    request: Request,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Cookie(None),
):

    try:
        logging.info(f"Token: {token}")
        # print(f"Token Cookie: {token_cookie}")
        print(f"Token: {token}")

        if not token:
            # No token found in header or cookie
            return JSONResponse(
                status_code=401, content={"message": "Authentication required"}
            )

        payload = jwt.decode(
            token, GoogleAuth.get_client_secret(), algorithms=["HS256"]
        )
        user_info = {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "picture": payload.get("picture"),
            "expire": payload.get("exp"),
        }

        return JSONResponse(
            content={
                "message": "Token verified",
                "data": user_info,
            }
        )
    except JWTError as e:
        logging.error(f"JWT error: {str(e)}")
        return JSONResponse(
            status_code=401, content={"message": "Invalid authentication credentials"}
        )
    except HTTPException as e:
        logging.error(f"Authentication error: {str(e)}")
        return JSONResponse(
            status_code=e.status_code,
            content={"message": str(e.detail)},
        )
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"},
        )
