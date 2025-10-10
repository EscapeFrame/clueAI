from fastapi import FastAPI
from app.api.routes import chat

app = FastAPI(title="LangChain FastAPI Server")

app.include_router(chat.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Success!"}