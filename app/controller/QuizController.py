"""
퀴즈 컨트롤러
Quiz Battle 기능을 위한 퀴즈 생성 API
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.model.QuizModel import QuizGenerationRequest, QuizGenerationResponse
from app.services.quiz_service import get_quiz_service
from app.config.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/quiz", tags=["Quiz"])


@router.post("/generate", response_model=QuizGenerationResponse)
async def generate_quiz(
    request: QuizGenerationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    퀴즈 생성 API
    
    - PostgreSQL에서 document_id로 문서를 가져와 ChromaDB에 저장
    - RAG를 사용하여 문서 기반 퀴즈 문제 생성 (멀티모달 지원)
    - 문서의 텍스트와 이미지를 활용하여 문제 생성
    
    Args:
        request: 퀴즈 생성 요청
        db: 데이터베이스 세션
        
    Returns:
        QuizGenerationResponse: 생성된 퀴즈 데이터
    """
    try:
        logger.info(f"Generating quiz for document: {request.document_id}, count: {request.question_count}")
        
        quiz_service = get_quiz_service()
        response = await quiz_service.generate_quiz(request, db)
        
        if response.status == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.message
            )
        
        logger.info(f"Successfully generated quiz with {len(response.data.questions)} questions")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/documents/ingest")
async def ingest_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    문서 인제스트 API
    
    PostgreSQL에서 문서(S3 또는 URL)를 가져와 ChromaDB에 저장
    
    Args:
        document_id: 문서 ID (UUID 문자열)
        db: 데이터베이스 세션
        
    Returns:
        성공 메시지
    """
    try:
        from uuid import UUID
        from app.repository.DocumentRepository import DocumentRepository
        from app.services.chroma_service import get_chroma_service
        from app.services.document_content_service import get_document_content_service
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        doc_id = UUID(document_id)
        
        doc_repo = DocumentRepository(db)
        document = await doc_repo.get_by_id(doc_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        content_service = get_document_content_service()
        content = await content_service.get_document_content(document)
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve document content from {document.type.value}"
            )
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(content)
        
        metadatas = [
            {
                "title": document.title,
                "type": document.type.value,
                "content_type": document.content_type or "",
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]
        
        # ChromaDB에 저장
        chroma_service = get_chroma_service()
        chroma_service.add_document_chunks(
            document_id=doc_id,
            chunks=chunks,
            metadatas=metadatas
        )
        
        logger.info(f"Document {document_id} ingested successfully ({len(chunks)} chunks)")
        
        return {
            "status": "success",
            "message": f"Document {document_id} ingested successfully",
            "document_type": document.type.value,
            "chunks_count": len(chunks)
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}"
        )
