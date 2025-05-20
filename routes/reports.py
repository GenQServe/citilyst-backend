import asyncio
from datetime import datetime, timezone
import logging
import os
import re
import sys
from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from helpers.common import create_verification_token
from sqlalchemy.ext.asyncio import AsyncSession
from helpers.db import db_connection, get_db
from helpers.jwt import JwtHelper
from models import reports
from services.auth import AuthService, PermissionChecker
import redis.asyncio as redis
from schemas.reports import DescriptionRequest, CategoryCreateRequest
from httpx import AsyncClient
from helpers.config import settings
from services.reports import ReportService
from permissions.model_permission import Reports as ReportPermissions
from helpers.common import generate_cuid

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

        request_payload = {
            "report_id": report_id,
            "category_name": category.get("name"),
            "description": generate_request.description,
            "location": generate_request.location,
        }
        # request tp n8n
        async with AsyncClient() as client:
            response = await client.post(
                f"{settings.N8N_API_URL}/webhook-test/generate-description",
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
