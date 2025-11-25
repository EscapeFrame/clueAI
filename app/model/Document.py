"""
Document Entity
PostgreSQL에 저장되는 문서 정보 (Spring Boot ERD 구조 반영)
"""

from sqlalchemy import Column, String, Text, DateTime, BigInteger, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.config.database import Base
from datetime import datetime
import uuid
import enum


class FileType(enum.Enum):
    """파일 타입"""
    FILE = "FILE"
    URL = "URL"


class Document(Base):
    """수업 자료 엔티티 (Spring Boot Document 구조)"""
    __tablename__ = "document"
    
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, name="document_id")
    title = Column(String(500), nullable=False)
    type = Column(SQLEnum(FileType), nullable=False)
    value = Column(String(1000), nullable=False)  
    original_file_name = Column(String(500), nullable=True, name="original_file_name")
    content_type = Column(String(200), nullable=True, name="content_type")
    size = Column(BigInteger, nullable=True)  
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, name="created_at")
    
    class_room_id = Column(UUID(as_uuid=True), ForeignKey("class_room.class_room_id"), nullable=False, name="class_room_id")
    directory_id = Column(UUID(as_uuid=True), ForeignKey("directory.directory_id"), nullable=True, name="directory_id")
    
    def __repr__(self):
        return f"<Document(document_id={self.document_id}, title={self.title}, type={self.type})>"
    
    @property
    def is_file(self) -> bool:
        """파일 타입 여부"""
        return self.type == FileType.FILE
    
    @property
    def is_url(self) -> bool:
        """URL 타입 여부"""
        return self.type == FileType.URL
