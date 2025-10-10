from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from app.core.config import settings

class LangChainService:
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.MODEL_NAME
        )
        self.memory = ConversationBufferMemory()
        self.conversation = ConversationChain(llm=self.llm, memory=self.memory)

    def chat(self, message: str) -> str:
        return self.conversation.predict(input=message)