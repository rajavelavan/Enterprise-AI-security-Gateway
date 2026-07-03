from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cryptographic AI Governance Gateway"
    API_V1_STR: str = "/api/v1"
    
    # Predefined sensitive keywords for Data Loss Prevention (DLP)
    # In a real-world scenario, this might be loaded from a database or a file
    SENSITIVE_KEYWORDS: List[str] = [
        "CONFIDENTIAL",
        "SSN",
        "CREDIT_CARD",
        "PASSWORD",
        "SECRET_KEY"
    ]

    class Config:
        case_sensitive = True

settings = Settings()
