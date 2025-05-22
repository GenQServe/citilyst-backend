import dis
import logging
import os
import secrets
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

    # create report
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
