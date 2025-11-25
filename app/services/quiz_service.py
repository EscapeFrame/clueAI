"""
퀴즈 생성 서비스
RAG 기반 문제 생성 로직
"""

from typing import List, Optional
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.llm.gemini_service import GeminiService
from app.services.chroma_service import get_chroma_service
from app.services.document_content_service import get_document_content_service
from app.services.multimodal_service import get_multimodal_service
from app.repository.DocumentRepository import DocumentRepository
from app.model.QuizModel import (
    QuizGenerationRequest,
    QuizQuestion,
    QuizOption,
    QuizData,
    QuizGenerationResponse
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class QuizService:
    """퀴즈 생성 서비스"""
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self.gemini_service = GeminiService()
        self.chroma_service = get_chroma_service()
        self.document_content_service = get_document_content_service()
        self.multimodal_service = get_multimodal_service()
        self.db = db
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        self.document_images_cache: Dict[UUID, List[Dict]] = {}
    
    async def generate_quiz(self, request: QuizGenerationRequest, db: AsyncSession) -> QuizGenerationResponse:
        """
        퀴즈 생성 (멀티모달 RAG 지원)
        
        Args:
            request: 퀴즈 생성 요청
            db: 데이터베이스 세션
            
        Returns:
            퀴즈 생성 응답
        """
        try:
            images = []
            if request.document_id:
                images = await self._ensure_document_in_chroma(
                    request.document_id, 
                    db,
                    use_multimodal=request.use_multimodal
                )
            
            context = await self._get_context(request.document_id)
            
            questions = await self._generate_questions_with_gemini(
                context=context,
                question_count=request.question_count,
                difficulty=request.difficulty,
                language=request.language,
                images=images if request.use_multimodal else []
            )
            
            return QuizGenerationResponse(
                data=QuizData(questions=questions),
                status="success",
                message=f"Successfully generated {len(questions)} questions"
            )
            
        except Exception as e:
            logger.error(f"Failed to generate quiz: {e}")
            return QuizGenerationResponse(
                data=QuizData(questions=[]),
                status="error",
                message=f"Failed to generate quiz: {str(e)}"
            )
    
    async def _get_context(self, document_id: UUID) -> str:
        """
        RAG를 사용하여 문맥 가져오기
        
        Args:
            document_id: 문서 ID
            
        Returns:
            문맥 텍스트
        """
        logger.info(f"Searching context from document_id: {document_id}")
        search_results = self.chroma_service.search_by_document_id(
            document_id=document_id,
            limit=10
        )
        
        if search_results:
            context = "\n\n---\n\n".join(search_results)
            logger.info(f"Found {len(search_results)} relevant chunks")
            return context
        else:
            logger.warning(f"No content found for document {document_id}")
            return ""
    
    async def _ensure_document_in_chroma(
        self, 
        document_id: UUID, 
        db: AsyncSession,
        use_multimodal: bool = True
    ) -> List[Dict]:
        """
        PostgreSQL에서 문서를 가져와서 ChromaDB에 저장되어 있는지 확인
        없으면 인제스트 (멀티모달 지원)
        
        Args:
            document_id: 문서 ID
            db: 데이터베이스 세션
            use_multimodal: 멀티모달(이미지) 사용 여부
            
        Returns:
            이미지 리스트
        """
        images = []
        
        try:
            existing = self.chroma_service.search_by_document_id(document_id, limit=1)
            if existing:
                logger.info(f"Document {document_id} already in ChromaDB")
                return self.document_images_cache.get(document_id, [])
            
            doc_repo = DocumentRepository(db)
            document = await doc_repo.get_by_id(document_id)
            
            if not document:
                logger.warning(f"Document {document_id} not found in PostgreSQL")
                return []
            
            content = await self.document_content_service.get_document_content(document)
            
            if not content:
                logger.warning(f"Failed to get content for document {document_id}")
                return []
            
            if use_multimodal:
                multimodal_data = await self.multimodal_service.extract_content_with_images(
                    document, content
                )
                content = multimodal_data["text"]
                images = multimodal_data["images"]
                
                self.document_images_cache[document_id] = images
                
                logger.info(f"Extracted {len(images)} images from document {document_id}")
            
            chunks = self.text_splitter.split_text(content)
            
            metadatas = [
                {
                    "title": document.title,
                    "type": document.type.value,
                    "content_type": document.content_type or "",
                    "chunk_index": i
                }
                for i in range(len(chunks))
            ]

            self.chroma_service.add_document_chunks(
                document_id=document_id,
                chunks=chunks,
                metadatas=metadatas,
                images=images
            )
            
            logger.info(f"Document {document_id} ingested to ChromaDB ({len(chunks)} chunks, {len(images)} images)")
            
            return images
            
        except Exception as e:
            logger.error(f"Failed to ensure document {document_id} in ChromaDB: {e}")
            return []
    
    async def _generate_questions_with_gemini(
        self,
        context: str,
        question_count: int,
        difficulty: str,
        language: str,
        images: List[Dict] = None
    ) -> List[QuizQuestion]:
        """
        Gemini를 사용하여 퀴즈 문제 생성 (멀티모달 지원)
        
        Args:
            context: RAG로 가져온 문맥
            question_count: 생성할 문제 수
            difficulty: 난이도
            language: 언어
            images: 이미지 리스트 (Optional)
            
        Returns:
            생성된 문제 리스트
        """
        if images is None:
            images = []
        
        system_messages = {
            "ko": "당신은 교육 퀴즈를 생성하는 전문가입니다. 주어진 자료를 바탕으로 학생들의 이해도를 평가할 수 있는 문제를 만들어주세요.",
            "en": "You are an expert in creating educational quizzes. Based on the given material, create questions that can assess students' understanding."
        }
        
        prompts = {
            "ko": """다음 학습 자료를 바탕으로 {question_count}개의 객관식 문제를 만들어주세요:

난이도: {difficulty}

학습 자료:
{context}

문제 작성 규칙:
1. 각 문제는 4개의 선택지를 가집니다 (0-3번)
2. 정답은 하나만 존재합니다
3. 난이도에 맞는 문제를 작성해주세요:
   - easy: 기본 개념과 정의를 확인하는 문제
   - medium: 개념 적용과 이해를 요구하는 문제
   - hard: 심화 사고와 분석을 요구하는 문제
4. 각 문제에 대한 명확한 해설을 작성해주세요
5. 제한 시간은 난이도에 따라 조정해주세요 (easy: 20초, medium: 30초, hard: 45초)

다음 JSON 형식으로 작성해주세요:
{{
  "questions": [
    {{
      "question_number": 1,
      "question_text": "문제 텍스트",
      "options": [
        {{"index": 0, "text": "선택지 1"}},
        {{"index": 1, "text": "선택지 2"}},
        {{"index": 2, "text": "선택지 3"}},
        {{"index": 3, "text": "선택지 4"}}
      ],
      "correct_answer": 0,
      "time_limit": 30,
      "explanation": "정답 해설",
      "difficulty": "{difficulty}"
    }}
  ]
}}

반드시 JSON 형식으로만 응답해주세요.""",
            "en": """Based on the following learning material, create {question_count} multiple-choice questions:

Difficulty: {difficulty}

Learning Material:
{context}

Question Guidelines:
1. Each question has 4 options (0-3)
2. Only one correct answer per question
3. Adjust difficulty appropriately:
   - easy: Basic concepts and definitions
   - medium: Concept application and understanding
   - hard: Advanced thinking and analysis
4. Provide clear explanations for each question
5. Time limits based on difficulty (easy: 20s, medium: 30s, hard: 45s)

Format in JSON:
{{
  "questions": [
    {{
      "question_number": 1,
      "question_text": "Question text",
      "options": [
        {{"index": 0, "text": "Option 1"}},
        {{"index": 1, "text": "Option 2"}},
        {{"index": 2, "text": "Option 3"}},
        {{"index": 3, "text": "Option 4"}}
      ],
      "correct_answer": 0,
      "time_limit": 30,
      "explanation": "Answer explanation",
      "difficulty": "{difficulty}"
    }}
  ]
}}

Respond only in JSON format."""
        }
        
        if not context:
            raise ValueError("Document content is empty. Cannot generate questions without content.")
        
        # 이미지가 있으면 프롬프트에 이미지 정보 추가
        image_context = ""
        if images:
            image_context = f"\n\n[첨부된 이미지 {len(images)}개]\n"
            for idx, img in enumerate(images[:5]):  # 최대 5개까지만
                image_context += f"- 이미지 {idx+1}: {img.get('caption', f'Page {img.get('page', 1)}')} (참조 가능)\n"
            context = context + image_context
        
        system_message = system_messages.get(language, system_messages["ko"])
        prompt_text = prompts.get(language, prompts["ko"])
        
        # 멀티모달: 이미지가 있으면 Gemini Vision API 사용
        if images and len(images) > 0:
            # Gemini에게 이미지와 함께 문제 생성 요청
            result = await self._generate_with_images(
                context, question_count, difficulty, language, images, prompt_text
            )
        else:
            # 텍스트만으로 문제 생성
            prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content=system_message),
                ("user", prompt_text)
            ])
            
            chain = prompt_template | self.gemini_service.llm | self.gemini_service.json_parser
            
            result = await chain.ainvoke({
                "question_count": question_count,
                "difficulty": difficulty,
                "context": context[:4000]  
            })
        
        # 결과 파싱
        try:
            questions = []
            for q_data in result.get("questions", []):
                options = [
                    QuizOption(index=opt["index"], text=opt["text"])
                    for opt in q_data.get("options", [])
                ]
                
                question = QuizQuestion(
                    question_number=q_data.get("question_number", len(questions) + 1),
                    question_text=q_data.get("question_text", ""),
                    question_image=q_data.get("question_image"),  # 멀티모달 이미지
                    options=options,
                    correct_answer=q_data.get("correct_answer", 0),
                    time_limit=q_data.get("time_limit", 30),
                    explanation=q_data.get("explanation", ""),
                    difficulty=q_data.get("difficulty", difficulty)
                )
                questions.append(question)
            
            logger.info(f"Generated {len(questions)} questions successfully")
            return questions
            
        except Exception as e:
            logger.error(f"Error parsing questions: {e}")
            return []
    
    async def _generate_with_images(
        self,
        context: str,
        question_count: int,
        difficulty: str,
        language: str,
        images: List[Dict],
        prompt_text: str
    ) -> dict:
        """
        이미지와 함께 문제 생성 (Gemini Vision)
        
        Args:
            context: 텍스트 문맥
            question_count: 문제 수
            difficulty: 난이도
            language: 언어
            images: 이미지 리스트
            prompt_text: 프롬프트 템플릿
            
        Returns:
            생성된 문제 JSON
        """
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage
            import base64
            
            # Gemini Vision 모델 사용
            vision_llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",  # 멀티모달 지원
                google_api_key=self.gemini_service.llm.google_api_key,
                temperature=0.7
            )
            
            # 프롬프트 생성
            user_prompt = prompt_text.format(
                question_count=question_count,
                difficulty=difficulty,
                context=context[:4000]
            )
            
            # 이미지 추가 안내
            user_prompt += f"\n\n**중요**: 첨부된 {len(images)}개의 이미지를 참고하여 문제를 생성해주세요. "
            user_prompt += "이미지와 관련된 문제를 포함하면 더 좋습니다. 이미지 기반 문제의 경우 question_image 필드에 해당 이미지의 인덱스를 넣어주세요."
            
            # HumanMessage에 이미지 포함
            content = [{"type": "text", "text": user_prompt}]
            
            # 이미지 추가 (최대 5개)
            for idx, img in enumerate(images[:5]):
                content.append({
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{img['data']}"
                })
            
            message = HumanMessage(content=content)
            
            # Gemini Vision 호출
            response = await vision_llm.ainvoke([message])
            
            # JSON 파싱
            import json
            result_text = response.content
            
            # JSON 추출 (마크다운 코드 블록 제거)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            
            # 이미지 참조를 실제 base64로 변환
            for q in result.get("questions", []):
                if "question_image" in q and isinstance(q["question_image"], int):
                    img_idx = q["question_image"]
                    if 0 <= img_idx < len(images):
                        q["question_image"] = images[img_idx]["data"]
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating with images: {e}")
            # 폴백: 텍스트만으로 생성
            prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content="당신은 교육 퀴즈를 생성하는 전문가입니다."),
                ("user", prompt_text)
            ])
            
            chain = prompt_template | self.gemini_service.llm | self.gemini_service.json_parser
            
            return await chain.ainvoke({
                "question_count": question_count,
                "difficulty": difficulty,
                "context": context[:4000]
            })


def get_quiz_service() -> QuizService:
    """QuizService 인스턴스 반환"""
    return QuizService()
