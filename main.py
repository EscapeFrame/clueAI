from fastapi import FastAPI
from app.controller import HealthCheck, AgentController, ChatController, QuizController
from app.config.database import Base, engine
from sqlalchemy.ext.asyncio import AsyncEngine

app = FastAPI()

app.include_router(AgentController.router)
app.include_router(ChatController.router)
app.include_router(QuizController.router)
app.include_router(HealthCheck.router)

# @app.on_event("startup")
# async def startup_event():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all) 

@app.get("/")
def read_root():
    return {"Hello": "World"}