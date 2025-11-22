from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar, List
from uuid import UUID
from datetime import datetime

T = TypeVar('T')

# ===== Request Models =====

class PlanningRequest(BaseModel):
    """Planning 단계 요청 모델"""
    studying_name: str
    learning_purpose: str
    main_words: List[str]
    links: List[str]

class WordItem(BaseModel):
    """목차 항목 모델"""
    priority: int
    index: str
    iconNumber: int

class FlowFeedbackRequest(BaseModel):
    """Flow 피드백 요청 모델"""
    words: List[WordItem]

class DocItem(BaseModel):
    """문서 항목 모델"""
    index: str
    content: str

class DocFeedbackRequest(BaseModel):
    """Doc 피드백 요청 모델"""
    docs: List[DocItem]

class GraphNode(BaseModel):
    """그래프 노드 모델"""
    id: int
    keyword: str
    links: List[int]

class ChatMessage(BaseModel):
    """채팅 메시지 모델"""
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str
    history: Optional[List[ChatMessage]] = []

# ===== Response Data Models =====

class AgentData(BaseModel):
    """Agent 생성 응답 데이터"""
    agent_id: UUID
    status: str
    created_at: datetime

class FlowData(BaseModel):
    """Flow 생성 응답 데이터"""
    words: List[WordItem]

class DocData(BaseModel):
    """Doc 생성 응답 데이터"""
    docs: List[DocItem]

class GraphData(BaseModel):
    """Graph 생성 응답 데이터"""
    nodes: List[GraphNode]

class CompleteData(BaseModel):
    """Complete 응답 데이터"""
    agent_id: UUID
    status: str
    final_markdown: str

class ChatData(BaseModel):
    """Chat 응답 데이터"""
    message: str
    history: List[ChatMessage]

class AllAgentData(BaseModel):
    """Agent 전체 데이터 조회 응답"""
    agent_id: UUID
    status: str
    planning: Optional[PlanningRequest] = None
    flow: Optional[FlowData] = None
    doc: Optional[DocData] = None
    graph: Optional[GraphData] = None

# ===== Generic Response Wrapper =====

class AgentResponse(BaseModel, Generic[T]):
    """Generic API 응답 래퍼"""
    success: bool = True
    message: str
    data: Optional[T] = None
    error: Optional[str] = None

# ===== Type Aliases for Cleaner Controller Code =====

AgentCreateResponse = AgentResponse[AgentData]
AgentGetResponse = AgentResponse[AllAgentData]
FlowResponse = AgentResponse[FlowData]
DocResponse = AgentResponse[DocData]
GraphResponse = AgentResponse[GraphData]
CompleteResponse = AgentResponse[CompleteData]
ChatResponse = AgentResponse[ChatData]
