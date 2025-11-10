from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.config.database import get_db
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config.config import settings

router = APIRouter(
  prefix="/health",
  tags=["Health Check"],
  responses={404: {"description" : "Not found"}}
)

@router.get("/db")
async def check_db(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "Database connection successful"}
    except Exception as e:
        return {"status": "error", "message": f"Database connection failed: {e}"}

@router.get("/gemini")
async def check_gemini():
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=settings.google_api_key)
        llm.invoke("hello")
        return {"status": "ok", "message": "Gemini connection successful"}
    except Exception as e:
        return {"status": "error", "message": f"Gemini connection failed: {e}"}