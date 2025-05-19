import logging
import os
import sys
from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from helpers.common import create_verification_token
from helpers.google_auth import GoogleAuth
from sqlalchemy.ext.asyncio import AsyncSession
from helpers.db import db_connection, get_db
from helpers.jwt import JwtHelper
from middleware.rbac_middleware import verify_role
from models.district import District
from schemas.district import (
    DistrictCreate,
    DistrictUpdate,
    DistrictResponse,
    DistrictListResponse,
)
from services.auth import AuthService, PermissionChecker
import redis.asyncio as redis
from helpers.config import settings
from services.district import DistrictService
from permissions.model_permission import Districts as DistrictPermissions


from services.users import UserService


routes_district = APIRouter(prefix="/districts", tags=["District"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@routes_district.post(
    "/",
    response_model=DistrictResponse,
    summary="Create district",
)
async def create_district(
    request: Request,
    district: DistrictCreate,
    dependencies=Depends(PermissionChecker([DistrictPermissions.permissions.CREATE])),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create district
    """
    try:
        district_service = DistrictService()
        try:
            existing_district = await district_service.get_district_by_name(
                db, district.name
            )
            if existing_district:
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={"message": "District already exists"},
                )
        except HTTPException as e:
            if e.status_code != 404:
                raise e
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
            content={"message": "Internal server error"},
        )


@routes_district.get(
    "/",
    response_model=DistrictListResponse,
    summary="Get all district",
)
async def get_all_district(
    request: Request,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([DistrictPermissions.permissions.READ])),
) -> JSONResponse:
    """
    Get all district
    """
    try:
        district_service = DistrictService()
        district = await district_service.get_all_districts(db)
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
            content={"message": "Internal server error"},
        )


# get all district with villages
@routes_district.get(
    "/with-villages",
    summary="Get all district with villages",
)
async def get_all_district_with_villages(
    request: Request,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([DistrictPermissions.permissions.READ])),
) -> JSONResponse:
    """
    Get all district with villages
    """
    try:
        district_service = DistrictService()
        district = await district_service.get_all_districts_with_villages(db)
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
            content={"message": "Internal server error"},
        )


@routes_district.get(
    "/{district_id}/villages",
    response_model=DistrictResponse,
    summary="Get district by name with villages",
)
async def get_district_by_id_with_villages(
    district_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([DistrictPermissions.permissions.READ])),
) -> JSONResponse:
    """
    Get district by name with villages
    """
    try:
        district_service = DistrictService()

        district = await district_service.get_district_by_id_with_villages(
            db, district_id
        )
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
        logging.error(f"Error getting district by name: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )


@routes_district.put(
    "/{district_id}",
    response_model=DistrictResponse,
    summary="Update district",
    description="Update an existing district by ID",
)
async def update_district(
    district_id: str,
    district: DistrictUpdate,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([DistrictPermissions.permissions.UPDATE])),
) -> JSONResponse:
    """
    Update district by ID
    """
    try:
        district_service = DistrictService()

        existing_district = await district_service.get_district_by_id(db, district_id)

        if district.name and district.name != existing_district["name"]:
            try:
                conflict = await district_service.get_district_by_name(
                    db, district.name
                )
                if conflict and conflict["id"] != district_id:
                    return JSONResponse(
                        status_code=status.HTTP_409_CONFLICT,
                        content={
                            "message": f"District with name '{district.name}' already exists"
                        },
                    )
            except HTTPException as e:
                raise e
        updated_district = await district_service.update_district(
            db, district_id, district
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "District updated successfully",
                "data": jsonable_encoder(updated_district),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error updating district: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )


@routes_district.delete(
    "/{district_id}",
    response_model=dict,
    summary="Delete district",
)
async def delete_district(
    district_id: str,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([DistrictPermissions.permissions.DELETE])),
) -> JSONResponse:
    """
    Delete district by ID
    """
    try:
        district_service = DistrictService()
        deleted_district = await district_service.delete_district(db, district_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "District deleted successfully",
                "data": jsonable_encoder(deleted_district),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error deleting district: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )
