import asyncio
from datetime import datetime, timedelta, timezone
import logging
from math import log
from typing import Optional, Union
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
    Form,
    File,
    UploadFile,
)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from helpers.common import create_verification_token
from sqlalchemy.ext.asyncio import AsyncSession
from helpers.db import db_connection, get_db
from helpers.jwt import JwtHelper
from models import reports
from models.district import District
from services.auth import AuthService, PermissionChecker
import redis.asyncio as redis
from schemas.reports import *
from httpx import AsyncClient
from helpers.config import settings
from services.reports import ReportService
from permissions.model_permission import Reports as ReportPermissions
from helpers.common import generate_cuid
from services.district import DistrictService
from services.users import UserService
from services.village import VillageService
from jinja2 import Environment, FileSystemLoader
from fastapi.templating import Jinja2Templates
from helpers.pdf_generator import generate_pdf_report
from helpers.cloudinary import upload_image, delete_image, upload_file

routes_report = APIRouter(prefix="/reports", tags=["Reports"])


@routes_report.get(
    "/category",
    summary="Get all report categories",
)
async def get_all_report_categories(
    request: Request,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([ReportPermissions.permissions.READ])),
) -> JSONResponse:
    """
    Get all report categories
    """
    try:
        reports_service = ReportService()
        categories = await reports_service.get_all_categories(db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Report categories retrieved successfully",
                "data": jsonable_encoder(categories),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error fetching report categories: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Failed to fetch report categories"},
        )


@routes_report.post(
    "/category",
    summary="Create report category",
)
async def create_report_category(
    request: Request,
    category_request: CategoryCreateRequest,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([ReportPermissions.permissions.CREATE])),
) -> JSONResponse:
    """
    Create report category
    """
    try:
        reports_service = ReportService()
        try:
            existing_category_key = await reports_service.get_category_by_key(
                db, category_request.key
            )
            if existing_category_key:
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={"message": "Category key already exists"},
                )
        except HTTPException as e:
            if e.status_code != 404:
                raise e

        category = await reports_service.create_category(db, category_request)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Report category created successfully",
                "data": jsonable_encoder(category),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error creating report category: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Failed to create report category"},
        )


@routes_report.post(
    "/generate-description",
    response_model=dict,
    summary="Generate description",
)
async def generate_description(
    request: Request,
    generate_request: DescriptionRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Generate description
    """
    try:
        # geerate report time
        report_id = generate_cuid()
        generate_request.report_id = report_id

        # get category
        reports_service = ReportService()
        category = await reports_service.get_category_by_key(
            db, generate_request.category_key
        )

        # get district
        district_service = DistrictService()
        district = await district_service.get_district_by_id(
            db, generate_request.district_id
        )
        if not district:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "District not found"},
            )
        # get village
        village_service = VillageService()
        village = await village_service.get_village_by_id(
            db, generate_request.village_id
        )

        request_payload = {
            "report_id": report_id,
            "category_name": category.get("name"),
            "district_name": district.get("name"),
            "village_name": village.get("name"),
            "description": generate_request.description,
            "location": generate_request.location,
        }
        # request tp n8n
        async with AsyncClient() as client:
            response = await client.post(
                f"{settings.N8N_API_URL}/webhook/generate-description",
                json=request_payload,
                timeout=20,
            )
            if response.status_code != 200:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"message": "Failed to generate description"},
                )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Description generated successfully",
                "data": jsonable_encoder(response.json()),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error generating description: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Failed to generate description"},
        )


# submit image
@routes_report.post("/images", summary="Upload images")
async def upload_images(
    request: Request,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([ReportPermissions.permissions.CREATE])),
) -> JSONResponse:
    """
    Upload images
    """

    try:
        if len(files) > 2:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "Only 2 images are allowed"},
            )

        # Upload images to Cloudinary
        upload_results = []
        for file in files:
            upload_result = await upload_image(file, folder="reports/images")
            if not upload_result:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"message": "Failed to upload image"},
                )
            upload_results.append(upload_result.get("secure_url"))

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Images uploaded successfully",
                "data": jsonable_encoder(upload_results),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error uploading images: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Failed to upload images"},
        )


@routes_report.post(
    "/",
    response_model=dict,
    summary="Submit report",
)
async def submit_report(
    request: Request,
    payload: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([ReportPermissions.permissions.CREATE])),
) -> JSONResponse:
    """
    Submit report
    """
    try:

        report_time = datetime.now(timezone.utc)
        report_time_converted = (
            report_time.replace(tzinfo=timezone.utc)
            .astimezone(timezone(timedelta(hours=7)))
            .strftime("%Y-%m-%d %H:%M:%S")
        )

        # Get user
        user_service = UserService()
        user = await user_service.get_user(db, payload.user_id)

        # Get category
        reports_service = ReportService()
        category = await reports_service.get_category_by_key(db, payload.category_key)
        if not category:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Category not found"},
            )

        # Get district and village
        district_service = DistrictService()
        district = await district_service.get_district_by_id(db, payload.district_id)
        if not district:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "District not found"},
            )
        village_service = VillageService()
        village = await village_service.get_village_by_id(db, payload.village_id)

        full_address = f"{payload.location}, Kel. {village.get('name')}, Kec. {district.get('name')}"

        report_data = {
            "report_id": payload.report_id,
            "report_time": report_time_converted,
            "user_name": user.get("name"),
            "user_email": user.get("email"),
            "category_name": category.get("name"),
            "district_name": district.get("name"),
            "village_name": village.get("name"),
            "description": payload.formal_description,
            "location": full_address,
            "attachments": payload.images_url,
        }

        # generate report pdf
        template_name = "report.html"
        output_file_path = f"outputs/report-{payload.report_id}.pdf"
        pdf_generated = await generate_pdf_report(
            template_name=template_name,
            output_file_path=output_file_path,
            report_data=report_data,
        )

        if not pdf_generated:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": "Failed to generate PDF report"},
            )
        logging.info(f"Report generated successfully: {pdf_generated}")
        # get fiile and upload to cloudinary

        # Upload PDF to Cloudinary
        # upload_result = await upload_file(
        #     output_file_path,
        #     folder="reports/pdf",
        #     public_id=settings.GOOGLE_DRIVE_FOLDER_ID,
        # )

        upload_result = await reports_service.upload_file_to_google_drive(
            file_path=output_file_path,
            folder_id=settings.GOOGLE_DRIVE_FOLDER_ID,
        )
        if not upload_result:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": "Failed to upload PDF to Cloudinary"},
            )
        logging.info(f"PDF uploaded successfully: {upload_result}")

        upload_data = ReportGenerateRequest(
            report_id=payload.report_id,
            user_id=payload.user_id,
            category_key=payload.category_key,
            formal_description=payload.formal_description,
            district_id=payload.district_id,
            village_id=payload.village_id,
            location=payload.location,
            file_url=upload_result.get("web_content_link"),
            images_url=payload.images_url,
        )

        # save report to db
        report = await reports_service.create_report(db, upload_data)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Report submitted successfully",
                "data": jsonable_encoder(report),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error generating report: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": " Internal server error"},
        )


# get all reports
@routes_report.get(
    "/",
    response_model=dict,
    summary="Get all reports",
)
async def get_all_reports(
    request: Request,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([ReportPermissions.permissions.READ])),
) -> JSONResponse:
    """
    Get all reports
    """
    try:
        reports_service = ReportService()
        reports = await reports_service.get_all_reports(db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Reports retrieved successfully",
                "data": jsonable_encoder(reports),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error fetching reports: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Failed to fetch reports"},
        )


@routes_report.put(
    "/{report_id}",
    response_model=dict,
    summary="Update report",
)
async def update_report(
    request: Request,
    report_id: str,
    payload: ReportUpdateRequest,
    db: AsyncSession = Depends(get_db),
    dependencies=Depends(PermissionChecker([ReportPermissions.permissions.UPDATE])),
) -> JSONResponse:
    """
    Update report
    """
    try:
        reports_service = ReportService()
        report = await reports_service.get_report_by_id(db, report_id)
        if not report:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Report not found"},
            )

        # Update report
        updated_report = await reports_service.update_report(db, report_id, payload)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Report updated successfully",
                "data": jsonable_encoder(updated_report),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        logging.error(f"Error updating report: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Failed to update report"},
        )
