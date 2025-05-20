import dis
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from helpers.db import get_db
from schemas.district import (
    VillageCreate,
    VillageUpdate,
    VillageResponse,
    VillageListResponse,
)
from services.district import DistrictService
from services.village import VillageService
from services.auth import PermissionChecker
from permissions.model_permission import Villages as VillagePermissions

routes_village = APIRouter(prefix="/villages", tags=["Village"])


@routes_village.post(
    "/",
    response_model=VillageResponse,
    summary="Create village",
)
async def create_village(
    request: Request,
    village: VillageCreate,
    dependencies=Depends(PermissionChecker([VillagePermissions.permissions.CREATE])),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create village
    """
    try:
        village_service = VillageService()
        district_service = DistrictService()

        district = await district_service.get_district_by_id(db, village.district_id)
        try:

            existing_village = await village_service.get_village_by_name(
                db, village.name
            )
            if existing_village:
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={"message": "Village already exists"},
                )
        except HTTPException as e:
            if e.status_code != 404:
                raise e
            village = await village_service.create_village(db, village)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Village created successfully",
                "data": jsonable_encoder(village),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error creating village: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )


@routes_village.get(
    "/",
    response_model=VillageListResponse,
    summary="Get all village",
)
async def get_all_village(
    request: Request,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([VillagePermissions.permissions.READ])),
) -> JSONResponse:
    """
    Get all village
    """
    try:
        village_service = VillageService()
        village = await village_service.get_all_villages(db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Village retrieved successfully",
                "data": jsonable_encoder(village),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error getting all village: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )


@routes_village.get(
    "/district/{district_id}",
    response_model=VillageListResponse,
    summary="Get village by district id",
)
async def get_village_by_district_id(
    district_id: str,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([VillagePermissions.permissions.READ])),
) -> JSONResponse:
    """
    Get village by district id
    """
    try:
        village_service = VillageService()
        village = await village_service.get_village_by_district_id(db, district_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Village retrieved successfully",
                "data": jsonable_encoder(village),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error getting village by district id: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )


@routes_village.put(
    "/{village_id}",
    response_model=VillageResponse,
    summary="Update village",
    description="Update an existing village by ID",
)
async def update_village(
    village_id: str,
    village: VillageUpdate,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([VillagePermissions.permissions.UPDATE])),
) -> JSONResponse:
    """
    Update village by ID
    """
    try:
        village_service = VillageService()

        existing_village = await village_service.get_village_by_id(db, village_id)

        if village.name and village.name != existing_village["name"]:
            try:
                conflict = await village_service.get_village_by_name(db, village.name)
                if conflict and conflict["id"] != village_id:
                    return JSONResponse(
                        status_code=status.HTTP_409_CONFLICT,
                        content={
                            "message": f"Village with name '{village.name}' already exists"
                        },
                    )
            except HTTPException as e:
                raise e
        updated_village = await village_service.update_village(db, village_id, village)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Village updated successfully",
                "data": jsonable_encoder(updated_village),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error updating village: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )


@routes_village.delete(
    "/{village_id}",
    response_model=dict,
    summary="Delete village",
)
async def delete_village(
    village_id: str,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([VillagePermissions.permissions.DELETE])),
) -> JSONResponse:
    """
    Delete village by ID
    """
    try:
        village_service = VillageService()
        deleted_village = await village_service.delete_village(db, village_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Village deleted successfully",
                "data": jsonable_encoder(deleted_village),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error deleting village: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )
