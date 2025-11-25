"""
Document Repository
PostgreSQL에서 문서를 조회하는 레포지토리
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.model.Document import Document
from uuid import UUID
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class DocumentRepository:
    """문서 레포지토리"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """
        문서 ID로 문서 조회
        
        Args:
            document_id: 문서 ID
            
        Returns:
            Document 엔티티 또는 None
        """
        try:
            result = await self.db.execute(
                select(Document).where(Document.document_id == document_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching document {document_id}: {e}")
            return None
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """
        모든 문서 조회
        
        Args:
            limit: 반환할 최대 문서 수
            offset: 시작 오프셋
            
        Returns:
            Document 리스트
        """
        try:
            result = await self.db.execute(
                select(Document).limit(limit).offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching documents: {e}")
            return []
    
    async def create(self, title: str, content: str, topic: Optional[str] = None) -> Document:
        """
        새 문서 생성
        
        Args:
            title: 문서 제목
            content: 문서 내용
            topic: 문서 주제
            
        Returns:
            생성된 Document
        """
        try:
            document = Document(
                title=title,
                content=content,
                topic=topic
            )
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)
            logger.info(f"Created document: {document.document_id}")
            return document
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            await self.db.rollback()
            raise
    
    async def delete(self, document_id: UUID) -> bool:
        """
        문서 삭제
        
        Args:
            document_id: 삭제할 문서 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            document = await self.get_by_id(document_id)
            if document:
                await self.db.delete(document)
                await self.db.commit()
                logger.info(f"Deleted document: {document_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            await self.db.rollback()
            return False
