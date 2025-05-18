from helpers.config import settings
import redis.asyncio as redis
import logging
from fastapi import Cookie, HTTPException, Request, Depends, status, APIRouter, File
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from services.users import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.users import UserCreate, UserUpdate
from typing import List, Optional
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from helpers.redis import (
    get_redis_client,
    set_redis_value,
    get_redis_value,
    delete_redis_value,
)
from helpers.db import get_db
from middleware.rbac_middleware import verify_role

routes_user = APIRouter(prefix="/user", tags=["User"])


@routes_user.get("/{user_id}", response_model=dict, summary="Get user profile by id")
async def get_user_by_id(
    user_id: str,
    token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_role(["admin"])),
) -> JSONResponse:
    """
    Get user profile by id
    """
    try:
        user_service = UserService()
        user = await user_service.get_user(db, user_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "User profile retrieved successfully",
                "data": jsonable_encoder(user),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})


@routes_user.put(
    "/{user_id}",
    response_model=dict,
    summary="Update user profile",
)
async def update_user(
    request: Request,
    user_id: str,
    user: UserUpdate,
    token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_role(["admin", "user"])),
) -> JSONResponse:
    """
    Update user profile
    """
    try:
        user_service = UserService()
        user_dict = user.dict(exclude_unset=True)
        updated_user = await user_service.update_user(db, user_id, user_dict)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "User profile updated successfully",
                "data": jsonable_encoder(updated_user),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )


@routes_user.put(
    "/{user_id}/profile-picture",
    response_model=dict,
    summary="Update user profile picture",
)
async def update_user_profile_picture(
    user_id: str,
    file: UploadFile = File(...),
    token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_role(["admin", "user"])),
) -> JSONResponse:
    """
    Update user profile picture
    """
    try:
        user_service = UserService()
        updated_user = await user_service.update_user_profile_picture(db, user_id, file)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "User profile picture updated successfully",
                "data": jsonable_encoder(updated_user),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error updating user profile picture: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )


@routes_user.delete(
    "/{user_id}",
    response_model=dict,
    summary="Delete user by id",
)
async def delete_user(
    user_id: str,
    token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_role(["admin"])),
) -> JSONResponse:
    """
    Delete user by id
    """
    try:
        user_service = UserService()
        await user_service.delete_user(db, user_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "User deleted successfully"},
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )
