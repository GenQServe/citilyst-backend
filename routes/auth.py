import logging
import os
import sys
from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.params import Cookie, Header
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from helpers.common import create_verification_token
from helpers.google_auth import GoogleAuth
from sqlalchemy.ext.asyncio import AsyncSession
from helpers.db import db_connection, get_db
from helpers.jwt import JwtHelper
from middleware.rbac_middleware import verify_role
from schemas.users import UserCreate
from services.auth import AuthService
import redis.asyncio as redis
from helpers.config import settings
from helpers.mailer import send_email_async, send_otp_email, send_otp_email_async
from schemas.otp import OTPRequest, OTPResendRequest, OTPResponse
from schemas.auth import BasicAuthRequest
from helpers.redis import get_redis_value, set_redis_value, delete_redis_value

from services.users import UserService

is_production = (
    os.getenv("ENVIRONMENT", "development").lower() == "production"
    or "--production" in sys.argv
)

routes_auth = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@routes_auth.get(
    "/me",
    summary="Get User Info",
    description="Get user info from token in cookie or Authorization header",
    response_model=None,
)
async def get_user_info(
    request: Request,
    token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService()
    user_service = UserService()
    jwt_helper = JwtHelper()
    try:
        if not token:
            # No token found in header or cookie
            return JSONResponse(
                status_code=401, content={"message": "Authentication required"}
            )

        token_value = str(token)

        if not token_value:
            return JSONResponse(
                status_code=401, content={"message": "Authentication required"}
            )

        # Decode token menggunakan jwt_helper yang sudah memiliki secret key
        payload = jwt_helper.decode(token_value)
        user_info = {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "picture": payload.get("picture"),
            "role": payload.get("role"),
            "is_verified": payload.get("is_verified"),
            "expire": payload.get("exp"),
        }

        user_id = user_info.get("id")
        if not user_id or not isinstance(user_id, str):
            return JSONResponse(
                status_code=401, content={"message": "Invalid user ID in token"}
            )
        user = await user_service.get_user(db, user_id)
        return JSONResponse(
            status_code=200,
            content={
                "message": "User info retrieved successfully",
                "data": jsonable_encoder(user),
            },
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


@routes_auth.post(
    "/login",
    summary="Login with Email and Password",
    description="Login with email and password",
)
async def login(
    request: Request,
    payload: BasicAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService()
    user_service = UserService()
    jwt_helper = JwtHelper()
    email = payload.email
    password = payload.password

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

        token = jwt_helper.create_token(user_data=user)

        response = JSONResponse(
            content={
                "message": "Login successful",
                "data": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "picture": user["image_url"],
                    "phone_number": user["phone_number"],
                    "address": user["address"],
                    "nik": user["nik"],
                    "is_verified": user["is_verified"],
                    "role": user["role"],
                },
            }
        )
        response.set_cookie(
            key="token",
            value=token,
            httponly=False,
            secure=False,
            samesite="lax",
            domain=request.url.hostname,
            max_age=3600,
            path="/",
        )
        return response
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


@routes_auth.post(
    "/register",
    summary="Register User",
    description="Register user with email and password",
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService()
    user_service = UserService()
    try:
        email = payload.email
        password = payload.password
        name = payload.name
        nik = payload.nik
        print(f"Data: {payload}")
        if not email or not password or not name:
            return JSONResponse(
                status_code=400,
                content={"message": "Email, password, and name are required"},
            )
        try:
            existing_user = await user_service.get_user_by_email(db, email)
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")

        except HTTPException as e:
            if e.status_code != 404:
                # create new user
                raise
            print(f"Creating user: {email}")
            user_data = {
                "email": email,
                "password": password,
                "name": name,
                "nik": nik,
            }

            created_user = await user_service.create_user(db, user_data)
            print(f"User created: {created_user}")

            token = create_verification_token(created_user["email"])
            logging.info(f"Verification token: {token}")
            # print(token)
            # email_verification_endpoint = (
            #     f"{payload.redirect_url}/auth/confirm-email/{token}/"
            # )
            # logging.info(f"Email verification endpoint: {email_verification_endpoint}")

            # Send OTP email
            otp_sent = False
            otp_error = None
            try:
                logging.info(f"Sending OTP to: {created_user['email']}")

                otp_sent = await send_otp_email(
                    email_to=created_user["email"],
                    user_id=created_user["id"],
                )
                if otp_sent:
                    logging.info(f"OTP sent successfully to {created_user['email']}")
                else:
                    logging.warning(f"OTP sending failed, but user was created")
            except Exception as e:
                otp_error = str(e)
                logging.error(f"Error sending OTP: {otp_error}")

            # Prepare response
            message = (
                "OTP sent to your email"
                if otp_sent
                else "Account created, but OTP sending failed"
            )

            return JSONResponse(
                content={
                    "message": message,
                    "data": {
                        "id": created_user["id"],
                        "email": created_user["email"],
                        "is_verified": False,
                        "otp_sent": otp_sent,
                    },
                }
            )
    except HTTPException as e:
        logging.error(f"Register error: {e.status_code}: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={"message": str(e.detail)},
        )
    except Exception as e:
        logging.error(f"Register error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"},
        )


@routes_auth.post(
    "/verify-otp",
    summary="Verify OTP",
    description="Verify OTP sent to email",
)
async def verify_otp(
    request: Request,
    payload: OTPRequest,
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService()
    user_service = UserService()
    jwt_helper = JwtHelper()
    try:
        email = payload.email
        otp = payload.otp
        print(f"Data: {payload}")
        if not email or not otp:
            return JSONResponse(
                status_code=400,
                content={"message": "Email and OTP are required"},
            )
        try:
            existing_user = await user_service.get_user_by_email(db, email)
            if not existing_user:
                raise HTTPException(status_code=400, detail="Email not registered")

            stored_otp = await get_redis_value(f"otp:{existing_user['id']}")
            if not stored_otp or stored_otp != otp:
                raise HTTPException(status_code=400, detail="Invalid OTP")

            update_data = {"is_verified": True}
            updated_user = await user_service.update_user(
                db, existing_user["id"], update_data
            )

            # Clear OTP from Redis
            await delete_redis_value(f"otp:{existing_user['id']}")

            token = jwt_helper.create_token(updated_user)

            response = JSONResponse(
                content={
                    "message": "OTP verified successfully",
                    "data": {
                        "id": updated_user["id"],
                        "email": updated_user["email"],
                        "name": updated_user["name"],
                        "picture": updated_user["image_url"],
                        "phone_number": updated_user["phone_number"],
                        "address": updated_user["address"],
                        "nik": updated_user["nik"],
                        "is_verified": updated_user["is_verified"],
                    },
                }
            )

            response.set_cookie(
                key="token",
                value=token,
                httponly=False,
                secure=False,
                samesite="lax",
                max_age=3600,
                domain=request.url.hostname,
                path="/",
            )
            return response
        except HTTPException as e:
            logging.error(f"Verify OTP error: {e.status_code}: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={"message": str(e.detail)},
            )
    except Exception as e:
        logging.error(f"Verify OTP error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"},
        )


@routes_auth.post(
    "/resend-otp",
    summary="Resend OTP",
    description="Resend OTP to email",
)
async def resend_otp(
    request: OTPResendRequest,
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService()
    user_service = UserService()
    try:
        email = request.email
        print(f"Data: {request}")
        if not email:
            return JSONResponse(
                status_code=400,
                content={"message": "Email is required"},
            )
        try:
            existing_user = await user_service.get_user_by_email(db, email)
            if not existing_user:
                raise HTTPException(status_code=400, detail="Email not registered")
            if existing_user["is_verified"]:
                raise HTTPException(status_code=400, detail="Email already verified")
            # Send OTP email
            otp_sent = False
            otp_error = None
            try:

                await delete_redis_value(f"otp:{existing_user['id']}")
                logging.info(f"Resending OTP to: {existing_user['email']}")
                otp_sent = await send_otp_email(
                    email_to=existing_user["email"],
                    user_id=existing_user["id"],
                )
                if otp_sent:
                    logging.info(f"OTP sent successfully to {existing_user['email']}")
                else:
                    logging.warning(f"OTP sending failed")
            except Exception as e:
                otp_error = str(e)
                logging.error(f"Error sending OTP: {otp_error}")

            message = "OTP resent to your email" if otp_sent else "Failed to resend OTP"

            return JSONResponse(
                content={
                    "message": message,
                    "data": {
                        "id": existing_user["id"],
                        "email": existing_user["email"],
                        "otp_sent": otp_sent,
                    },
                }
            )
        except HTTPException as e:
            logging.error(f"Resend OTP error: {e.status_code}: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={"message": str(e.detail)},
            )
    except Exception as e:
        logging.error(f"Resend OTP error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"},
        )


@routes_auth.get(
    "/google",
    summary="Login with Google",
    description="Login with Google OAuth2.0",
)
async def login_google(request: Request, redirect_uri: str, path: Optional[str] = None):
    try:
        auth_service = AuthService()
        safe_path = path if path is not None else ""
        result = await auth_service.login_google(redirect_uri, safe_path, request)
        return result
    except HTTPException as e:
        logging.error(f"Login with Google error: {e.status_code}: {e.detail}")
        if e.status_code == 400:
            return JSONResponse(
                status_code=e.status_code,
                content={"message": str(e.detail)},
            )
        elif e.status_code == 500:
            return JSONResponse(
                status_code=e.status_code,
                content={"message": "Internal server error"},
            )
        return JSONResponse(
            status_code=e.status_code,
            content={"message": str(e.detail)},
        )
    except Exception as e:
        logging.error(f"Login with Google error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"},
        )


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
        jwt_helper = JwtHelper()
        logging.info(f"Authenticating with Google code: {code}")
        logging.info(f"Authenticating with Google state: {state}")
        logging.info(
            f"Authenticating with Google request url: {request.headers.get('origin')}"
        )

        redirect_uri = await get_redis_value(f"redirect_uri:{state}")
        if not redirect_uri:
            raise HTTPException(
                status_code=400, detail="Invalid or expired state token"
            )

        path = await get_redis_value(f"path:{state}")
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
                "image_url": user_info.get("picture"),
                "email": user_info.get("email"),
            }
            updated_user = await user_service.update_user(
                db, existing_user["id"], update_data
            )
            user_info["id"] = updated_user["id"]
            user_info["name"] = updated_user["name"]
            user_info["image_url"] = updated_user["image_url"]
            user_info["is_verified"] = updated_user["is_verified"]
            user_info["nik"] = updated_user["nik"]
            user_info["role"] = updated_user["role"]
        else:
            logging.info(f"Creating new user: {user_info['email']}")
            create_data = {
                "email": user_info["email"],
                "name": user_info.get("name"),
                "image_url": user_info.get("picture"),
            }
            created_user = await user_service.create_user(db, create_data)
            user_info["id"] = created_user["id"]
            user_info["name"] = created_user["name"]
            user_info["image_url"] = created_user["image_url"]
            user_info["is_verified"] = created_user["is_verified"]
            user_info["nik"] = created_user["nik"]
            user_info["role"] = created_user["role"]
        token = jwt_helper.create_token(user_info)
        frontend_url = redirect_uri

        is_profile_complete = (
            user_info.get("name")
            and user_info.get("email")
            and user_info.get("is_verified") is True
            and user_info.get("nik") is not None
        )

        custom_path = "/"
        if not is_profile_complete:
            custom_path = "/profile"

        if frontend_url.endswith("/"):
            if custom_path.startswith("/"):
                frontend_url += custom_path[1:]
            else:
                frontend_url += custom_path
        else:
            if not custom_path.startswith("/"):
                frontend_url += "/" + custom_path
            else:
                frontend_url += custom_path
        redirect_response = RedirectResponse(url=frontend_url)
        redirect_response.set_cookie(
            key="token",
            value=token,
            httponly=False,
            secure=False,
            samesite="lax",
            max_age=3600,
            domain=request.url.hostname,
            path="/",
        )
        await delete_redis_value(f"redirect_uri:{state}")
        if path:
            await delete_redis_value(f"path:{state}")

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
    authorization: Optional[str] = Header(),
    token: str = Cookie(),
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

        secret = GoogleAuth.get_client_secret()
        if not secret:
            return JSONResponse(
                status_code=401,
                content={"message": "Authentication secret not configured"},
            )
        payload = jwt.decode(token, secret, algorithms=["HS256"])
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
