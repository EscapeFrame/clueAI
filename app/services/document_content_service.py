"""
Document Service
문서 내용을 가져오는 서비스 (S3 또는 URL)
"""

import logging
from typing import Optional
from uuid import UUID
import aiohttp
import boto3
from botocore.exceptions import ClientError

from app.model.Document import Document, FileType
from app.config.config import settings

logger = logging.getLogger(__name__)


class DocumentContentService:
    """문서 내용을 가져오는 서비스"""
    
    def __init__(self):
        """config에서 S3 설정 읽기"""
        self.s3_bucket = settings.aws_s3_bucket
        self.s3_client = None
        
        if self.s3_bucket:
            try:
                # AWS 자격증명이 있으면 사용, 없으면 기본 자격증명 체인 사용
                if settings.aws_access_key_id and settings.aws_secret_access_key:
                    self.s3_client = boto3.client(
                        's3',
                        region_name=settings.aws_region,
                        aws_access_key_id=settings.aws_access_key_id,
                        aws_secret_access_key=settings.aws_secret_access_key
                    )
                else:
                    self.s3_client = boto3.client('s3', region_name=settings.aws_region)
                
                logger.info(f"S3 client initialized with bucket: {self.s3_bucket}")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}")
    
    async def get_document_content(self, document: Document) -> str:
        """
        문서 내용 가져오기
        
        Args:
            document: Document 엔티티
            
        Returns:
            문서 내용 (텍스트)
        """
        try:
            if document.type == FileType.FILE:
                # S3에서 파일 내용 가져오기
                return await self._get_from_s3(document.value)
            elif document.type == FileType.URL:
                # URL에서 내용 가져오기
                return await self._get_from_url(document.value)
            else:
                logger.error(f"Unknown document type: {document.type}")
                return ""
        except Exception as e:
            logger.error(f"Failed to get document content: {e}")
            return ""
    
    async def _get_from_s3(self, s3_key: str) -> str:
        """
        S3에서 파일 내용 가져오기
        
        Args:
            s3_key: S3 객체 키
            
        Returns:
            파일 내용
        """
        if not self.s3_client or not self.s3_bucket:
            logger.error("S3 client not initialized")
            return ""
        
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
            content = response['Body'].read()
            
            # 텍스트로 디코딩 시도
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    return content.decode('cp949')  # 한글 인코딩
                except UnicodeDecodeError:
                    logger.error(f"Failed to decode S3 file: {s3_key}")
                    return ""
        except ClientError as e:
            logger.error(f"S3 error: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error reading from S3: {e}")
            return ""
    
    async def _get_from_url(self, url: str) -> str:
        """
        URL에서 내용 가져오기
        
        Args:
            url: 문서 URL
            
        Returns:
            페이지 내용
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()
                        return content
                    else:
                        logger.error(f"Failed to fetch URL {url}: Status {response.status}")
                        return ""
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error fetching URL {url}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error fetching URL {url}: {e}")
            return ""


# 싱글톤 인스턴스
_document_content_service: Optional[DocumentContentService] = None


def get_document_content_service() -> DocumentContentService:
    """DocumentContentService 싱글톤 인스턴스 반환"""
    global _document_content_service
    if _document_content_service is None:
        _document_content_service = DocumentContentService()
    return _document_content_service
