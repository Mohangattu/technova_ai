"""FastAPI entry point: uvicorn app.main:app --host 0.0.0.0 --port 8000."""

from collections import Counter
from contextlib import asynccontextmanager
import logging
import threading
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import ROOT, Settings
from app.core.security import authorize
from app.services.knowledge import KnowledgeService

logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=2000)

    @field_validator("query")
    @classmethod
    def strip_query(cls, value):
        if not value.strip():
            raise ValueError("Please enter a question.")
        return value.strip()


class Source(BaseModel):
    document_id: str
    title: str
    department: str
    section: str
    version: str
    excerpt: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    grounded: bool
    verification_reason: str
    mode: Literal["local", "groq"]
    route: str
    retry_count: int
    latency_ms: float


def create_app(settings=None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(application):
        application.state.knowledge = KnowledgeService(settings)
        application.state.query_slots = threading.BoundedSemaphore(settings.query_limit)
        yield

    application = FastAPI(title="TechNova AI", version="1.0.0", lifespan=lifespan)
    application.state.settings = settings

    @application.get("/health", tags=["System"])
    def health():
        return {"status": "ok"}

    @application.get("/api/status", dependencies=[Depends(authorize)], tags=["System"])
    def status(request: Request):
        service = request.app.state.knowledge
        documents = service.visible_documents()
        return {
            "mode": settings.rag_mode,
            "access_level": settings.access_level,
            "document_count": len(documents),
            "departments": dict(sorted(Counter(d.metadata.department for d in documents).items())),
        }

    @application.get("/api/documents", dependencies=[Depends(authorize)], tags=["Knowledge"])
    def documents(
        request: Request,
        search: str = Query(default="", max_length=200),
        department: str | None = None,
    ):
        return {"documents": request.app.state.knowledge.list_documents(search, department)}

    @application.get(
        "/api/documents/{document_id}", dependencies=[Depends(authorize)], tags=["Knowledge"]
    )
    def document(request: Request, document_id: str):
        result = request.app.state.knowledge.document(document_id)
        if not result:
            raise HTTPException(
                status_code=404, detail="Document not found or unavailable to your workspace."
            )
        return result

    @application.post(
        "/api/query",
        response_model=QueryResponse,
        dependencies=[Depends(authorize)],
        tags=["Assistant"],
    )
    def query(payload: QueryRequest, request: Request):
        slots = request.app.state.query_slots
        if not slots.acquire(blocking=False):
            raise HTTPException(
                status_code=429, detail="The assistant is busy. Please try again shortly."
            )
        try:
            return request.app.state.knowledge.query(payload.query)
        except Exception:
            logger.exception("RAG query failed")
            raise HTTPException(
                status_code=503,
                detail="The assistant couldn’t complete this request. Please try again.",
            ) from None
        finally:
            slots.release()

    application.mount("/assets", StaticFiles(directory=ROOT / "frontend"), name="assets")

    @application.get("/", include_in_schema=False)
    def index():
        return FileResponse(ROOT / "frontend" / "index.html")

    return application


app = create_app()
