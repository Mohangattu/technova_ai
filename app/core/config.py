"""Environment settings; paths are resolved independently of the launch directory."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    rag_mode: Literal["local", "groq"] = "local"
    knowledge_dir: Path = ROOT / "data" / "raw"
    vectorstore_dir: Path = ROOT / "vectorstore" / "chroma"
    access_level: Literal["EMPLOYEE", "MANAGER", "AI_ENGINEER", "DEVOPS", "SECURITY", "ADMIN"] = (
        "EMPLOYEE"
    )
    technova_api_key: str = ""
    groq_api_key: str = ""
    groq_base_url: str = ""
    query_limit: int = Field(default=2, ge=1, le=16)
