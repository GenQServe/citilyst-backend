import dis
import logging
import os
import secrets
from tkinter import E
from urllib.parse import urlencode
import redis.asyncio as redis
import requests
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException
from typing import List, Optional
from models.users import User
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from helpers.redis import set_redis_value, get_redis_value, delete_redis_value
from schemas.reports import CategoryCreateRequest, ReportGenerateRequest
from models.reports import *
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from helpers.config import settings


class ReportService:
    async def get_all_categories(self, db: AsyncSession) -> List[dict]:
        try:
            result = await db.execute(
                select(ReportCategory).order_by(ReportCategory.created_at.desc())
            )
            categories = result.scalars().all()
            categories_list = [category.to_dict() for category in categories]
            return categories_list
        except Exception as e:
            logging.error(f"Error fetching categories: {str(e)}")
            raise Exception(f"Failed to fetch categories: {str(e)}")

    async def get_category_by_id(self, db: AsyncSession, category_id: str) -> dict:
        try:
            result = await db.execute(
                select(ReportCategory).where(ReportCategory.id == category_id)
            )
            category_model = result.scalars().first()
            if not category_model:
                raise HTTPException(status_code=404, detail="Category not found")
            return category_model.to_dict()
        except HTTPException as e:
            logging.warning(
                f"HTTP error in get_category_by_id: {e.status_code} - {e.detail}"
            )
            raise e
        except Exception as e:
            logging.error(f"Error fetching category: {str(e)}")
            raise Exception(f"Failed to fetch category: {str(e)}")

    async def get_category_by_key(self, db: AsyncSession, key: str) -> dict:
        try:
            result = await db.execute(
                select(ReportCategory).where(ReportCategory.key == key)
            )
            category_model = result.scalars().first()
            if not category_model:
                raise HTTPException(status_code=404, detail="Category not found")
            return category_model.to_dict()
        except HTTPException as e:
            logging.warning(
                f"HTTP error in get_category_by_key: {e.status_code} - {e.detail}"
            )
            raise e
        except Exception as e:
            logging.error(f"Error fetching category: {str(e)}")
            raise Exception(f"Failed to fetch category: {str(e)}")

    async def create_category(
        self, db: AsyncSession, category: CategoryCreateRequest
    ) -> dict:
        try:
            category_model = ReportCategory(key=category.key, name=category.name)
            db.add(category_model)
            await db.commit()
            await db.refresh(category_model)
            return category_model.to_dict()
        except Exception as e:
            logging.error(f"Error creating category: {str(e)}")
            raise Exception(f"Failed to create category: {str(e)}")

    async def upload_file_to_google_drive(self, file_path: str, folder_id: str) -> dict:
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise HTTPException(
                    status_code=404, detail=f"File not found: {file_path}"
                )

            # Get credentials
            credentials = self._get_google_credentials()

            # Upload to Google Drive
            service = build("drive", "v3", credentials=credentials)
            file_metadata = {
                "name": os.path.basename(file_path),
                "parents": [folder_id],
            }
            media = MediaFileUpload(file_path, mimetype="application/pdf")
            file = (
                service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, webContentLink, webViewLink",
                )
                .execute()
            )
            file_id = file.get("id")
            web_content_link = file.get("webContentLink")
            web_view_link = file.get("webViewLink")

            logging.info(
                f"File uploaded successfully to Google Drive: {web_content_link}"
            )
            return {
                "file_id": file_id,
                "web_content_link": web_content_link,
                "web_view_link": web_view_link,
            }
        except HttpError as e:
            logging.error(f"Google Drive API error: {e}")
            raise Exception(f"Google Drive API error: {str(e)}")
        except Exception as e:
            logging.error(f"Error uploading file to Google Drive: {str(e)}")
            raise Exception(f"Failed to upload file: {str(e)}")

    def _get_google_credentials(self):
        """
        Get Google API credentials from service account JSON file.
        """
        from google.oauth2 import service_account

        # Path to the service account JSON file
        service_account_file = settings.GOOGLE_SERVICE_ACCOUNT_FILE

        # Check if credentials file exists
        if not os.path.exists(service_account_file):
            logging.error(
                f"Google service account file not found: {service_account_file}"
            )
            raise HTTPException(
                status_code=500, detail="Google Drive service account file not found"
            )

        # Define the required scopes
        SCOPES = ["https://www.googleapis.com/auth/drive"]

        try:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=SCOPES
            )
            return credentials
        except Exception as e:
            logging.error(f"Error loading Google credentials: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to load Google credentials: {str(e)}"
            )

    async def create_report(
        self, db: AsyncSession, report: ReportGenerateRequest
    ) -> dict:
        try:
            report_model = Report(
                report_id=report.report_id,
                user_id=report.user_id,
                category_key=report.category_key,
                formal_description=report.formal_description,
                district_id=report.district_id,
                village_id=report.village_id,
                location=report.location,
                file_url=report.file_url,
                images_url=report.images_url,
            )
            db.add(report_model)
            await db.commit()
            await db.refresh(report_model)
            return report_model.to_dict()
        except Exception as e:
            logging.error(f"Error creating report: {str(e)}")
            raise Exception(f"Failed to create report: {str(e)}")
