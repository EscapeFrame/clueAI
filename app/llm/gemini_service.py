from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.config.config import settings
from typing import List
import logging

logger = logging.getLogger(__name__)


class GeminiService:
    """Gemini LLM 서비스"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=settings.google_api_key,
            temperature=0.7
        )
        self.json_parser = JsonOutputParser()
    
    async def generate_flow(self, studying_name: str, learning_purpose: str, 
                           main_words: List[str], links: List[str]) -> dict:
        """목차(Flow) 생성"""
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessage(content="당신은 교육 자료 목차를 생성하는 전문가입니다."),
            ("user", """다음 정보를 바탕으로 학습 목차를 생성해주세요:

학습 주제: {studying_name}
학습 목적: {learning_purpose}
주요 키워드: {main_words}
참고 링크: {links}

목차는 3-7개의 항목으로 구성하되, 다음 JSON 형식으로 작성해주세요:
{{
  "words": [
    {{"priority": 1, "index": "첫 번째 목차 제목", "iconNumber": 1}},
    {{"priority": 2, "index": "두 번째 목차 제목", "iconNumber": 2}}
  ]
}}

iconNumber는 1-5 사이의 값으로 해당 항목의 중요도나 난이도를 나타냅니다.
반드시 JSON 형식으로만 응답해주세요.""")
        ])
        
        try:
            chain = prompt_template | self.llm | self.json_parser
            
            result = await chain.ainvoke({
                "studying_name": studying_name,
                "learning_purpose": learning_purpose,
                "main_words": ', '.join(main_words),
                "links": ', '.join(links)
            })
            
            return result
        except Exception as e:
            logger.error(f"Error generating flow: {e}")
            raise
    
    async def generate_doc(self, studying_name: str, learning_purpose: str,
                          main_words: List[str], flow_words: List[dict], links: List[str]) -> dict:
        """본문(Doc) 생성 - 각 목차별로 분할된 JSON 형식"""
        # flow_words에서 목차 제목들을 추출
        flow_text = '\n'.join([f"{word['priority']}. {word['index']}" for word in flow_words])
        
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessage(content="당신은 교육 자료를 작성하는 전문가입니다. 각 목차별로 상세한 수업 자료를 작성해주세요."),
            ("user", """다음 정보를 바탕으로 각 목차별로 상세한 학습 자료를 작성해주세요:

학습 주제: {studying_name}
학습 목적: {learning_purpose}
주요 키워드: {main_words}
참고 링크: {links}

다음 목차 구조를 **반드시 그대로** 따라 작성해주세요:
{flow_text}

작성 규칙:
1. **각 목차마다 별도의 항목으로 작성**
2. 각 목차에 대해 전문적인 Markdown 형식 설명 작성
3. 실용적인 예제와 함께 설명 (코드가 필요하면 ```언어명 블록 사용)
4. 중요한 개념은 **굵게**, 용어는 `인라인 코드`로 강조
5. 필요시 리스트(-, 1.), 표, 인용문(>) 등을 활용하여 가독성 향상

다음 JSON 형식으로 작성해주세요:
{{
  "docs": [
    {{"index": "첫 번째 목차 제목", "content": "첫 번째 목차에 대한 상세한 Markdown 형식 내용..."}},
    {{"index": "두 번째 목차 제목", "content": "두 번째 목차에 대한 상세한 Markdown 형식 내용..."}},
    ...
  ]
}}

**중요**: 
- 위에 제시된 목차의 제목과 순서를 정확히 지켜주세요
- 각 content는 Markdown 형식으로 작성하되, ## 제목은 빼고 본문만 작성
- 반드시 JSON 형식으로만 응답해주세요""")
        ])
        
        try:
            chain = prompt_template | self.llm | self.json_parser
            
            result = await chain.ainvoke({
                "studying_name": studying_name,
                "learning_purpose": learning_purpose,
                "main_words": ', '.join(main_words),
                "links": '\n'.join([f"- {link}" for link in links]) if links else "없음",
                "flow_text": flow_text
            })
            
            return result
        except Exception as e:
            logger.error(f"Error generating doc: {e}")
            raise
    
    async def chat(self, message: str, history: List[dict]) -> str:
        """채팅 응답 생성"""
        try:
            prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content="당신은 친절하고 도움이 되는 AI 어시스턴트입니다."),
                MessagesPlaceholder(variable_name="history"),
                ("user", "{message}")
            ])
            
            # 히스토리를 LangChain 메시지 형식으로 변환
            history_messages = []
            for msg in history:
                if msg['role'] == "user":
                    history_messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == "assistant":
                    history_messages.append(AIMessage(content=msg['content']))
            
            chain = prompt_template | self.llm
            
            response = await chain.ainvoke({
                "history": history_messages,
                "message": message
            })
            
            return response.content
        except Exception as e:
            logger.error(f"Error during chat: {e}")
            raise
