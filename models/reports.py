from datetime import date, datetime, timezone
from enum import Enum
from sqlalchemy import Column, DateTime, ForeignKey, String, ARRAY, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as SQLEnum
from helpers.common import generate_cuid
from helpers.db import Base
from models import village


"""
Report types:
- pelayanan publik
- infrastruktur rusak
- tindakan korupsi
- lingkungan
- pelanggaran prosedur

Status :
- pending
- resolved
- rejected
"""


class ReportStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    resolved = "resolved"
    rejected = "rejected"


class Report(Base):
    __tablename__ = "tbl_reports"

    id = Column(String(25), primary_key=True, default=generate_cuid)
    user_id = Column(String(25), ForeignKey("tbl_users.id"), nullable=False)
    category_key = Column(
        String(50), ForeignKey("tbl_report_category.key"), nullable=False
    )
    district_id = Column(String(25), ForeignKey("tbl_district.id"), nullable=True)
    village_id = Column(
        String(25), ForeignKey("tbl_village.id", ondelete="CASCADE"), nullable=True
    )

    formal_description = Column(String(255), nullable=False)
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.pending, nullable=False)
    feedback = Column(String(255), nullable=True)
    images_url = Column(ARRAY(String), nullable=True)
    location = Column(String(255), nullable=True)
    file_url = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), default=func.now())

    user = relationship("User", back_populates="reports")
    category = relationship("ReportCategory", back_populates="reports")
    district = relationship("District", back_populates="reports")
    village = relationship("Village", back_populates="reports")
    images = relationship(
        "ReportImage", back_populates="report", cascade="all, delete-orphan"
    )

    def __init__(
        self,
        report_id: str,
        user_id: str,
        category_key: str,
        formal_description: str,
        status: ReportStatus = ReportStatus.pending,
        feedback: str = None,
        district_id: str = None,
        village_id: str = None,
        file_url: str = None,
        images_url: list = None,
        location: str = None,
    ):
        self.id = report_id
        self.user_id = user_id
        self.category_key = category_key
        self.formal_description = formal_description
        self.status = status
        self.feedback = feedback
        self.district_id = district_id
        self.village_id = village_id
        self.file_url = file_url
        self.images_url = images_url or []
        self.location = location
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_key": self.category_key,
            "district_id": self.district_id,
            "village_id": self.village_id,
            "formal_description": self.formal_description,
            "status": self.status,
            "feedback": self.feedback,
            "images": self.images_url,
            "file_url": self.file_url,
            "location": self.location,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_dict_with_user(self):
        data = self.to_dict()
        data["user"] = self.user.to_dict() if self.user else None
        return data


class ReportCategory(Base):
    __tablename__ = "tbl_report_category"

    id = Column(String(25), primary_key=True, default=generate_cuid)
    key = Column(String(50), unique=True, nullable=False)
    name = Column(String(50), nullable=False)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    reports = relationship("Report", back_populates="category")

    def __init__(self, key: str, name: str):
        self.key = key
        self.name = name
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_dict_with_reports(self):
        data = self.to_dict()
        data["reports"] = [r.to_dict() for r in self.reports] if self.reports else []
        return data


class ReportImage(Base):
    __tablename__ = "tbl_report_image"

    id = Column(String(25), primary_key=True, default=generate_cuid)
    report_id = Column(
        String(25), ForeignKey("tbl_reports.id", ondelete="CASCADE"), nullable=False
    )
    image_url = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    report = relationship("Report", back_populates="images")

    def __init__(self, report_id: str, image_url: str):
        self.report_id = report_id
        self.image_url = image_url
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "image_url": self.image_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
