from fastapi import APIRouter, HTTPException, status
from app.model.AgentModel import (
    ChatRequest,
    ChatResponse
)
from app.service.AgentService import AgentService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}}
)

agent_service = AgentService()


@router.post("", response_model=ChatResponse)
async def chat_with_gemini(chat_request: ChatRequest):
    """
    Gemini와 자유롭게 대화하기

    사용자의 메시지와 대화 히스토리를 받아 Gemini의 응답을 반환합니다.
    히스토리를 포함하여 요청하면 문맥을 유지한 대화가 가능합니다.

    - **message**: 사용자의 현재 질문/메시지
    - **history**: 이전 대화 히스토리 (선택사항)
    """
    try:
        chat_data = await agent_service.chat(chat_request)
        return ChatResponse(
            success=True,
            message="Chat completed successfully",
            data=chat_data
        )
    except Exception as e:
        logger.error(f"Error during chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
