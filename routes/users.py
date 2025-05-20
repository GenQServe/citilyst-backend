from helpers.config import settings
import redis.asyncio as redis
import logging
from fastapi import Cookie, HTTPException, Request, Depends, status, APIRouter, File
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from services.users import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.users import UserCreate, UserUpdate, UserCreateByAdmin
from typing import List, Optional, Annotated
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from services.auth import get_role_permissions, PermissionChecker
from helpers.redis import (
    get_redis_client,
    set_redis_value,
    get_redis_value,
    delete_redis_value,
)
from helpers.db import get_db
from middleware.rbac_middleware import verify_role
from permissions.model_permission import Users, UsersProfile

routes_user = APIRouter(prefix="/user", tags=["User"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# create user
@routes_user.post(
    "/",
    response_model=dict,
    summary="Create user",
)
async def create_user(
    request: Request,
    user: UserCreateByAdmin,
    dependencies=Depends(PermissionChecker([Users.permissions.CREATE])),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:

    try:
        user_service = UserService()

        try:
            existing_user = await user_service.get_user_by_email(db, user.email)
            if existing_user:
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={"message": "User already exists"},
                )
        except HTTPException as e:
            if e.status_code != 404:
                raise e

        created_user = await user_service.create_user(db, user.dict(exclude_unset=True))

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "User created successfully",
                "data": jsonable_encoder(created_user),
            },
        )
    except HTTPException as e:
        logging.warning(f"HTTP error in create_user: {e.status_code} - {e.detail}")
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error creating user: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Internal server error: {str(e)}"},
        )


@routes_user.get("/{user_id}", response_model=dict, summary="Get user profile by id")
async def get_user_by_id(
    user_id: str,
    dependencies=Depends(PermissionChecker([Users.permissions.READ])),
    db: AsyncSession = Depends(get_db),
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


@routes_user.get(
    "/",
    response_model=List[dict],
    summary="Get all users",
)
async def get_all_users(
    request: Request,
    dependencies=Depends(PermissionChecker([Users.permissions.READ])),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get all users
    """
    try:
        user_service = UserService()
        users = await user_service.get_all_users(db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Users retrieved successfully",
                "data": jsonable_encoder(users),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error getting all users: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )


@routes_user.put(
    "/{user_id}",
    response_model=dict,
    summary="Update user profile",
)
async def update_user(
    request: Request,
    user_id: str,
    user: UserUpdate,
    dependencies=Depends(PermissionChecker([Users.permissions.UPDATE])),
    db: AsyncSession = Depends(get_db),
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
    request: Request,
    user_id: str,
    dependencies=Depends(PermissionChecker([UsersProfile.permissions.UPDATE])),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
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
    request: Request,
    user_id: str,
    dependencies=Depends(PermissionChecker([Users.permissions.DELETE])),
    db: AsyncSession = Depends(get_db),
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
