import logging
import os
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.params import Cookie, Header
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from helpers.google_auth import GoogleAuth
from sqlalchemy.ext.asyncio import AsyncSession
from helpers.db import db_connection
from services.auth import AuthService
import redis.asyncio as redis

routes_auth = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


@routes_auth.get(
    "/google",
    summary="Login with Google",
    description="Login with Google OAuth2.0",
)
async def login_google(redirect_uri: str, path: Optional[str] = None):
    auth_service = AuthService()
    result = await auth_service.login_google(redirect_uri, path)
    return result


@routes_auth.get(
    "/google/callback",
    summary="Auth with Google Callback",
    description="Auth with Google OAuth2.0 Callback",
)
async def auth_google(
    code: str,
    state: str,
    response: Response,
    db: AsyncSession = Depends(db_connection.get_db),
):
    try:
        auth_service = AuthService()
        logging.info(f"Authenticating with Google code: {code}")
        logging.info(f"Authenticating with Google state: {state}")
        print("Authenticating with Google code: ", code)
        print("Authenticating with Google state: ", state)

        # Retrieve redirect URI from Redis
        redirect_uri = await redis_client.get(f"redirect_uri:{state}")
        if not redirect_uri:
            raise HTTPException(
                status_code=400, detail="Invalid or expired state token"
            )

        # Get path if it exists
        path = await redis_client.get(f"path:{state}")
        user_info = await auth_service.authenticate_with_google(code)
        if not user_info:
            raise HTTPException(
                status_code=400, detail="Failed to authenticate with Google"
            )
        logging.info(f"User info: {user_info}")
        print("User info: ", user_info)
        # Check if user already exists in database
        existing_user = await auth_service.get_user_by_email(db, user_info["email"])
        if existing_user:
            # User already exists, update user info if necessary
            await auth_service.update_user(
                db, existing_user.id, user_info["name"], user_info["picture"]
            )
        else:
            # User does not exist, create a new user
            logging.info(f"Creating new user: {user_info['email']}")
            print("Creating new user: ", user_info["email"])
            # create user in database
            created_user = await auth_service.create_user(
                db, user_info["email"], user_info["name"], user_info["picture"]
            )
            user_info["id"] = created_user.id
            user_info["name"] = created_user.name
            user_info["picture"] = created_user.picture

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
            max_age=86400,  # 1 day
            path="/",
        )
        await redis_client.delete(f"redirect_uri:{state}")
        if path:
            await redis_client.delete(f"path:{state}")

        return redirect_response
    except HTTPException as e:
        logging.error(f"Auth error: {str(e)}")
        error_url = f"{redirect_uri}?auth/login?status=error"
        return RedirectResponse(url=error_url)
    except Exception as e:
        logging.error(f"Auth error: {str(e)}")
        # Redirect to frontend with error
        # frontend_url = GoogleAuth.get_frontend_uri() or "http://localhost:3000"
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
