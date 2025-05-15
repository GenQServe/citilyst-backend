from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, ARRAY, func
from sqlalchemy.orm import relationship
from helpers.common import generate_cuid
from helpers.db import Base


class Report(Base):
    __tablename__ = "tbl_reports"

    id = Column(String(25), primary_key=True, default=generate_cuid)
    user_id = Column(String(25), ForeignKey("tbl_users.id"), nullable=False)
    report_type = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    feedback = Column(String(255), nullable=True)
    images_url = Column(ARRAY, nullable=True)
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="reports")

    def __init__(self, user_id: str, report_type: str, report_data: dict):
        self.user_id = user_id
        self.report_type = report_type
        self.report_data = report_data
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "report_type": self.report_type,
            "description": self.description,
            "status": self.status,
            "feedback": self.feedback,
            "images_url": self.images_url,
            "location": self.location,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    """
    Report types:
    - pelayanan publik
    - infrastruktur rusak
    - tindakan korupsi
    - lingkungan
    - pelanggaran prosedur

    Status :
    - pending
    - processing
    - rejected
    - success
    """
