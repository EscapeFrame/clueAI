"""
Quiz Battle 모델 정의
Spring Boot 백엔드와의 연동을 위한 요청/응답 모델
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID

class QuizGenerationRequest(BaseModel):
    """퀴즈 생성 요청"""
    document_id: UUID = Field(..., description="RAG에 사용할 문서 ID")
    question_count: int = Field(default=10, ge=1, le=50, description="생성할 문제 수")
    difficulty: str = Field(default="medium", description="난이도 (easy, medium, hard)")
    language: str = Field(default="ko", description="언어 (ko, en)")
    use_multimodal: bool = Field(default=True, description="멀티모달(이미지 포함) 사용 여부")


class QuizOption(BaseModel):
    """선택지"""
    index: int = Field(..., description="선택지 번호 (0부터 시작)")
    text: str = Field(..., description="선택지 텍스트")


class QuizQuestion(BaseModel):
    """퀴즈 문제"""
    question_number: int = Field(..., description="문제 번호")
    question_text: str = Field(..., description="문제 텍스트")
    question_image: Optional[str] = Field(None, description="문제 이미지 (base64)")
    options: List[QuizOption] = Field(..., description="선택지 목록 (4개)")
    correct_answer: int = Field(..., ge=0, le=3, description="정답 인덱스 (0-3)")
    time_limit: int = Field(default=30, description="제한 시간 (초)")
    explanation: str = Field(..., description="정답 해설")
    difficulty: str = Field(..., description="난이도 (easy, medium, hard)")


class QuizData(BaseModel):
    """퀴즈 데이터"""
    questions: List[QuizQuestion] = Field(..., description="문제 목록")


class QuizGenerationResponse(BaseModel):
    """퀴즈 생성 응답"""
    data: QuizData
    status: str = Field(default="success", description="상태 (success, error)")
    message: Optional[str] = Field(None, description="메시지")


class DocumentChunk(BaseModel):
    """문서 청크 (ChromaDB 저장용)"""
    document_id: UUID = Field(..., description="문서 ID")
    chunk_index: int = Field(..., description="청크 인덱스")
    content: str = Field(..., description="청크 내용")
    metadata: dict = Field(default_factory=dict, description="메타데이터")


class DocumentIngestRequest(BaseModel):
    """문서 인제스트 요청"""
    document_id: UUID = Field(..., description="문서 ID")
