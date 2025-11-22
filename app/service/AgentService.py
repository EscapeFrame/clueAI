from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Dict
from app.model.AgentModel import (
    PlanningRequest,
    AgentData,
    AllAgentData,
    FlowData,
    DocData,
    CompleteData,
    WordItem,
    DocItem,
    FlowFeedbackRequest,
    DocFeedbackRequest,
    ChatRequest,
    ChatData,
    ChatMessage
)
from app.llm import GeminiService
import logging

logger = logging.getLogger(__name__)

class AgentStore:
    """Agent 데이터 저장 클래스"""
    def __init__(self):
        self.agent_id: UUID
        self.status: str = "PLANNING_COMPLETED"
        self.created_at: datetime
        self.updated_at: datetime
        self.planning: Optional[PlanningRequest] = None
        self.flow: Optional[FlowData] = None
        self.doc: Optional[DocData] = None

class AgentService:
    def __init__(self):
        self.agents: Dict[UUID, AgentStore] = {}
        self.gemini_service = GeminiService()

    async def create_agent(self, planning_request: PlanningRequest) -> AgentData:
        """
        1단계: Agent 생성 (Planning 단계)
        POST /api/v1/agents
        """
        agent_id = uuid4()
        now = datetime.now()

        agent_store = AgentStore()
        agent_store.agent_id = agent_id
        agent_store.status = "PLANNING_COMPLETED"
        agent_store.created_at = now
        agent_store.updated_at = now
        agent_store.planning = planning_request

        self.agents[agent_id] = agent_store

        logger.info(f"Agent created: {agent_id}")

        return AgentData(
            agent_id=agent_id,
            status="PLANNING_COMPLETED",
            created_at=now
        )

    async def get_agent(self, agent_id: UUID) -> Optional[AllAgentData]:
        """
        Agent 전체 상태 조회
        GET /api/v1/agents/{agent_id}
        """
        agent_store = self.agents.get(agent_id)
        if not agent_store:
            return None

        return AllAgentData(
            agent_id=agent_store.agent_id,
            status=agent_store.status,
            planning=agent_store.planning,
            flow=agent_store.flow,
            doc=agent_store.doc
        )

    async def create_flow(self, agent_id: UUID) -> Optional[FlowData]:
        """
        2단계: Flow 생성 (목차 생성)
        POST /api/v1/agents/{agent_id}/flow
        """
        agent_store = self.agents.get(agent_id)
        if not agent_store or not agent_store.planning:
            return None

        planning = agent_store.planning

        try:
            flow_data = await self.gemini_service.generate_flow(
                studying_name=planning.studying_name,
                learning_purpose=planning.learning_purpose,
                main_words=planning.main_words,
                links=planning.links
            )
            words = [WordItem(**word) for word in flow_data.get("words", [])]
            flow = FlowData(words=words)

            agent_store.flow = flow
            agent_store.status = "FLOW_GENERATED"
            agent_store.updated_at = datetime.now()

            logger.info(f"Flow created for agent: {agent_id}")
            return flow

        except Exception as e:
            logger.error(f"Error creating flow: {e}")
            default_words = [
                WordItem(priority=1, index=f"{planning.studying_name} 개요", iconNumber=1),
                WordItem(priority=2, index="주요 개념", iconNumber=2),
                WordItem(priority=3, index="실습 예제", iconNumber=3)
            ]
            flow = FlowData(words=default_words)
            agent_store.flow = flow
            agent_store.status = "FLOW_GENERATED"
            agent_store.updated_at = datetime.now()
            return flow

    async def update_flow(self, agent_id: UUID, feedback: FlowFeedbackRequest) -> Optional[FlowData]:
        """
        3단계: Flow 피드백
        PATCH /api/v1/agents/{agent_id}/flow
        """
        agent_store = self.agents.get(agent_id)
        if not agent_store:
            return None

        flow = FlowData(words=feedback.words)
        agent_store.flow = flow
        agent_store.status = "FLOW_UPDATED"
        agent_store.updated_at = datetime.now()

        logger.info(f"Flow updated for agent: {agent_id}")
        return flow

    async def create_doc(self, agent_id: UUID) -> Optional[DocData]:
        """
        4단계: Doc 생성 (본문 생성)
        POST /api/v1/agents/{agent_id}/doc
        """
        agent_store = self.agents.get(agent_id)
        if not agent_store or not agent_store.flow or not agent_store.planning:
            return None

        planning = agent_store.planning
        flow = agent_store.flow

        try:
            # flow에서 나온 목차 정보를 모두 전달 (priority, index, iconNumber)
            flow_words = [
                {
                    "priority": word.priority,
                    "index": word.index,
                    "iconNumber": word.iconNumber
                } 
                for word in flow.words
            ]
            doc_data = await self.gemini_service.generate_doc(
                studying_name=planning.studying_name,
                learning_purpose=planning.learning_purpose,
                main_words=planning.main_words,
                flow_words=flow_words,
                links=planning.links
            )
            
            # JSON 응답을 DocItem 리스트로 변환
            docs = [DocItem(**doc) for doc in doc_data.get("docs", [])]
            doc = DocData(docs=docs)

            agent_store.doc = doc
            agent_store.status = "DOC_GENERATED"
            agent_store.updated_at = datetime.now()

            logger.info(f"Doc created for agent: {agent_id}")
            return doc

        except Exception as e:
            logger.error(f"Error creating doc: {e}")
            # 기본 문서 생성
            default_docs = [
                DocItem(index=word.index, content=f"{word.index}에 대한 상세 설명입니다.")
                for word in flow.words
            ]
            doc = DocData(docs=default_docs)
            agent_store.doc = doc
            agent_store.status = "DOC_GENERATED"
            agent_store.updated_at = datetime.now()
            return doc

    async def update_doc(self, agent_id: UUID, feedback: DocFeedbackRequest) -> Optional[DocData]:
        """
        5단계: Doc 피드백
        PATCH /api/v1/agents/{agent_id}/doc
        """
        agent_store = self.agents.get(agent_id)
        if not agent_store:
            return None

        doc = DocData(docs=feedback.docs)
        agent_store.doc = doc
        agent_store.status = "DOC_UPDATED"
        agent_store.updated_at = datetime.now()

        logger.info(f"Doc updated for agent: {agent_id}")
        return doc

    async def complete(self, agent_id: UUID) -> Optional[CompleteData]:
        """
        6단계: 최종 마크다운 생성
        POST /api/v1/agents/{agent_id}/complete
        """
        agent_store = self.agents.get(agent_id)
        if not agent_store or not agent_store.planning or not agent_store.doc:
            return None

        planning = agent_store.planning
        doc = agent_store.doc

        # DocItem 리스트를 하나의 Markdown 문서로 조합
        markdown = f"# {planning.studying_name}\n\n"
        markdown += f"## 학습 목적\n{planning.learning_purpose}\n\n"
        markdown += f"## 주요 키워드\n{', '.join(planning.main_words)}\n\n"
        
        for doc_item in doc.docs:
            markdown += f"## {doc_item.index}\n\n{doc_item.content}\n\n"
        
        if planning.links:
            markdown += "## 참고 자료\n\n"
            for link in planning.links:
                markdown += f"- {link}\n"
        
        agent_store.status = "COMPLETED"
        agent_store.updated_at = datetime.now()

        logger.info(f"Agent completed: {agent_id}")

        return CompleteData(
            agent_id=agent_id,
            status="COMPLETED",
            final_markdown=markdown
        )

    async def chat(self, chat_request: ChatRequest) -> ChatData:
        """
        채팅 엔드포인트
        Gemini와 자유롭게 대화할 수 있습니다.
        """
        try:
            history = [{"role": msg.role, "content": msg.content} for msg in chat_request.history]
            assistant_message = await self.gemini_service.chat(
                message=chat_request.message,
                history=history
            )

            updated_history = chat_request.history.copy()
            updated_history.append(ChatMessage(role="user", content=chat_request.message))
            updated_history.append(ChatMessage(role="assistant", content=assistant_message))

            logger.info(f"Chat completed. History length: {len(updated_history)}")

            return ChatData(
                message=assistant_message,
                history=updated_history
            )

        except Exception as e:
            logger.error(f"Error during chat: {e}")
            raise e
