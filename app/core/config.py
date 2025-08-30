from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import logging
import os
from dotenv import load_dotenv


# Bootstrap env and logging once for core package
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crm_agent")


@dataclass
class Config:
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB: str = os.getenv("MONGO_DB", "crm")
    ALLOWED_COLLECTIONS: List[str] = tuple(os.getenv("ALLOWED_COLLECTIONS", "leads,tasks,notes,call_logs,activity").split(","))

    SWAGGER_SPEC_URL: Optional[str] = os.getenv("SWAGGER_SPEC_URL")
    SWAGGER_BASE_URL: Optional[str] = os.getenv("SWAGGER_BASE_URL")
    SWAGGER_AUTH_HEADER: Optional[str] = os.getenv("SWAGGER_AUTH_HEADER")
    SWAGGER_AUTH_VALUE: Optional[str] = os.getenv("SWAGGER_AUTH_VALUE")

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "json_stub")  # json_stub|openai
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    METABASE_SITE_URL: Optional[str] = os.getenv("METABASE_SITE_URL")
    METABASE_USERNAME: Optional[str] = os.getenv("METABASE_USERNAME")
    METABASE_PASSWORD: Optional[str] = os.getenv("METABASE_PASSWORD")
    METABASE_SESSION_TOKEN: Optional[str] = os.getenv("METABASE_SESSION_TOKEN")
    METABASE_EMBED_SECRET: Optional[str] = os.getenv("METABASE_EMBED_SECRET")


CFG = Config()


