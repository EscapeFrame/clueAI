from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str
    google_api_key: str
    
    aws_s3_bucket: Optional[str] = None
    aws_region: str = "ap-northeast-2"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"  # 정의되지 않은 필드 무시

settings = Settings()