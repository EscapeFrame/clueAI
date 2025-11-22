from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from app.model.AgentModel import (
    PlanningRequest,
    AgentCreateResponse,
    AgentGetResponse,
    FlowResponse,
    DocResponse,
    CompleteResponse,
    FlowFeedbackRequest,
    DocFeedbackRequest
)
from app.service.AgentService import AgentService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/agents",
    tags=["Agent"],
    responses={404: {"description": "Not found"}}
)

agent_service = AgentService()


@router.post("", response_model=AgentCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(planning_request: PlanningRequest):
    """
    1단계: Agent 생성 (Planning 단계)

    사용자로부터 학습 주제, 목적, 키워드, 참고 링크를 받아 Agent를 생성합니다.
    """
    try:
        agent_data = await agent_service.create_agent(planning_request)
        return AgentCreateResponse(
            success=True,
            message="Agent created successfully",
            data=agent_data
        )
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{agent_id}", response_model=AgentGetResponse)
async def get_agent(agent_id: UUID):
    """
    Agent 전체 상태 조회
    작업 중단 후 다시 이어하기 위해 Agent의 현재까지 모든 데이터를 조회합니다.
    """
    try:
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )

        return AgentGetResponse(
            success=True,
            message="Agent retrieved successfully",
            data=agent
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{agent_id}/flow", response_model=FlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow(agent_id: UUID):
    """
    2단계: Flow 생성 (목차 생성)

    Agent의 planning 데이터를 기반으로 학습 목차를 생성합니다.
    """
    try:
        flow = await agent_service.create_flow(agent_id)
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found or planning not completed"
            )

        return FlowResponse(
            success=True,
            message="Flow successfully generated",
            data=flow
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/{agent_id}/flow", response_model=FlowResponse)
async def update_flow(agent_id: UUID, feedback: FlowFeedbackRequest):
    """
    3단계: Flow 피드백

    AI가 생성한 목차를 사용자가 수정하여 업데이트합니다.
    """
    try:
        flow = await agent_service.update_flow(agent_id, feedback)
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )

        return FlowResponse(
            success=True,
            message="Flow feedback applied",
            data=flow
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{agent_id}/doc", response_model=DocResponse, status_code=status.HTTP_201_CREATED)
async def create_doc(agent_id: UUID):
    """
    4단계: Doc 생성 (본문 생성)

    Agent의 flow 데이터를 기반으로 각 목차에 대한 상세 본문을 생성합니다.
    """
    try:
        doc = await agent_service.create_doc(agent_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found or flow not generated"
            )

        return DocResponse(
            success=True,
            message="Documentation created successfully",
            data=doc
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating documentation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/{agent_id}/doc", response_model=DocResponse)
async def update_doc(agent_id: UUID, feedback: DocFeedbackRequest):
    """
    5단계: Doc 피드백

    AI가 생성한 본문을 사용자가 수정하여 업데이트합니다.
    
    Request Body:
    {
        "docs": [
            {"index": "목차 제목", "content": "수정된 내용..."},
            ...
        ]
    }
    """
    try:
        doc = await agent_service.update_doc(agent_id, feedback)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )

        return DocResponse(
            success=True,
            message="Documentation feedback applied",
            data=doc
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating documentation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{agent_id}/complete", response_model=CompleteResponse)
async def complete_agent(agent_id: UUID):
    """
    6단계: 제작 완료

    모든 단계를 종합하여 최종 마크다운 학습 자료를 생성합니다.
    """
    try:
        complete_data = await agent_service.complete(agent_id)
        if not complete_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found or required data missing"
            )

        return CompleteResponse(
            success=True,
            message="Lesson markdown generated successfully",
            data=complete_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
