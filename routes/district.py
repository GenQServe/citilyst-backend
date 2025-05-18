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
from schemas.district import (
    DistrictCreate,
    DistrictUpdate,
    DistrictResponse,
    DistrictResponseList,
    DistrictListResponse,
    VillageCreate,
    VillageUpdate,
    VillageResponse,
    VillageResponseList,
)
from services.auth import AuthService
import redis.asyncio as redis
from helpers.config import settings

from schemas.feedback_user import FeedbackUserRequest
from helpers.redis import get_redis_value, set_redis_value, delete_redis_value

from services.users import UserService


routes_district = APIRouter(prefix="/district", tags=["District"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@routes_district.post(
    "/",
    response_model=DistrictResponse,
    summary="Create district",
)
async def create_district(
    request: Request,
    district: DistrictCreate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_role(["admin"])),
) -> JSONResponse:
    """
    Create district
    """
    try:
        district_service = DistrictService()
        district = await district_service.create_district(db, district)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "District created successfully",
                "data": jsonable_encoder(district),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error creating district: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Failed to create district: {str(e)}"},
        )


# route untuk update district
@routes_district.put(
    "/{district_id}",
    response_model=DistrictResponse,
    summary="Update district",
)
async def update_district(
    request: Request,
    district_id: str,
    district: DistrictUpdate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_role(["admin"])),
) -> JSONResponse:
    """
    Update district
    """
    try:
        district_service = DistrictService()
        district = await district_service.update_district(db, district_id, district)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "District updated successfully",
                "data": jsonable_encoder(district),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error updating district: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Failed to update district: {str(e)}"},
        )


@routes_district.get(
    "/",
    response_model=DistrictResponseList,
    summary="Get all district",
)
async def get_all_district(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_role(["admin", "user"])),
) -> JSONResponse:
    """
    Get all district
    """
    try:
        district_service = DistrictService()
        district = await district_service.get_all_district(db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "District retrieved successfully",
                "data": jsonable_encoder(district),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error getting all district: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Failed to get all district: {str(e)}"},
        )
