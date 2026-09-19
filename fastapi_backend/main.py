import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi.responses import StreamingResponse

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    status,
    Request,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base, engine, get_db
import secrets
from models import ChatMessage, ChatSession

logger = logging.getLogger(
    "govsaathi.fastapi"
)

bearer_scheme = HTTPBearer(auto_error=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )

    from pathlib import Path

    from rag.src.config import INDEX_DIR
    from rag.src.pipeline import RagPipeline

    print(
        "Loading GovSaathi RAG pipeline..."
    )

    app.state.rag_pipeline = RagPipeline(
        index_dir=Path(INDEX_DIR),
    )

    print(
        "GovSaathi RAG pipeline loaded."
    )

    yield

    app.state.rag_pipeline = None
    await engine.dispose()


app = FastAPI(
    title="GovSaathi Mock API",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=5000)
    language: str = "en"


class Citation(BaseModel):
    title: str
    source: str
    page: int | None = None


class ChatResponse(BaseModel):
    session_id: str
    query: str
    answer: str
    citations: list[Citation]
    detected_language: str
    created_at: datetime

class SessionResponse(BaseModel):
    session_id: str
    token: str


@app.get("/")
async def root():
    return {
        "message": "GovSaathi FastAPI mock API is running"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }

async def get_authenticated_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: AsyncSession = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Use Bearer authentication",
        )

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.token == credentials.credentials,
        )
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session or token",
        )

    return session


async def verify_session_token(
    session_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: AsyncSession = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Use Bearer authentication",
        )

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.token == credentials.credentials,
        )
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session or token",
        )

    return session


async def verify_chat_session(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
        )

    scheme, separator, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not separator or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Use Authorization: Bearer <token>",
        )

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == request.session_id,
            ChatSession.token == token,
        )
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session or token",
        )

    return session



@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: Request,
    chat_request: ChatRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: AsyncSession = Depends(get_db),
):
    
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
    )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Use Bearer authentication",
        )

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id
            == chat_request.session_id,
            ChatSession.token
            == credentials.credentials,
        )
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session or token",
        )

    rag_pipeline = request.app.state.rag_pipeline

    if rag_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline is not available",
        )

    try:
        rag_result = rag_pipeline.answer_query(
            chat_request.query,
            top_k=5,
        )
        
    except Exception as exc:
        logger.exception(
            "RAG request failed for query: %s",
            chat_request.query,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="RAG request failed",
        ) from exc
    

    answer = rag_result.get(
        "answer",
        "No answer was generated.",
    )

    citations = []
    seen_sources = set()

    for source in rag_result.get(
        "sources",
        [],
    ):
        file_name = source.get(
            "file_name",
            "Unknown source",
        )

        source_path = source.get(
            "source",
            "Unknown source",
        )

        source_key = (
            str(file_name).strip().lower()
        )

        if source_key in seen_sources:
            continue

        seen_sources.add(source_key)

        citations.append(
            {
                "title": file_name,
                "source": source_path,
                "page": None,
            }
        )


    created_at = datetime.now(timezone.utc)

    user_message = ChatMessage(
        session_id=chat_request.session_id,
        role="user",
        content=chat_request.query,
        detected_language=chat_request.language,
        created_at=created_at,
    )

    assistant_message = ChatMessage(
        session_id=chat_request.session_id,
        role="assistant",
        content=answer,
        citations_json=json.dumps(citations),
        detected_language=chat_request.language,
        created_at=created_at,
    )


    db.add_all(
        [
            user_message,
            assistant_message,
        ]
    )

    await db.commit()

    return {
        "session_id": chat_request.session_id,
        "query": chat_request.query,
        "answer": answer,
        "citations": citations,
        "detected_language": chat_request.language,
        "created_at": created_at,
}


@app.post("/api/chat/stream")
async def stream_chat(
    request: Request,
    chat_request: ChatRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: AsyncSession = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Use Bearer authentication",
        )

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == chat_request.session_id,
            ChatSession.token == credentials.credentials,
        )
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session or token",
        )

    rag_pipeline = request.app.state.rag_pipeline

    if rag_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline is not available",
        )

    async def generate():
        try:
            for chunk in rag_pipeline.stream_answer_query(
                chat_request.query,
                top_k=5,
            ):
                yield chunk

        except Exception:
            logger.exception(
                "Streaming RAG request failed for query: %s",
                chat_request.query,
            )
            yield "\n\nRAG request failed."

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
    )


@app.get("/api/history/{session_id}")
async def get_history(
    session_id: str,
    _: ChatSession = Depends(verify_session_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at, ChatMessage.id)
    )

    messages = result.scalars().all()

    return {
        "session_id": session_id,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "text": message.content,
                "citations": (
                    json.loads(message.citations_json)
                    if message.citations_json
                    else []
                ),
                "detected_language": message.detected_language,
                "created_at": message.created_at,
            }
            for message in messages
        ],
    }


@app.get("/api/db-check")
async def db_check(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import text

    result = await db.execute(
        text("SELECT current_database(), current_user")
    )

    database_name, user_name = result.one()

    return {
        "database": database_name,
        "user": user_name,
    }


@app.post("/api/session", response_model=SessionResponse)
async def create_session(
    db: AsyncSession = Depends(get_db),
):
    session_id = secrets.token_urlsafe(24)
    token = secrets.token_urlsafe(32)

    new_session = ChatSession(
        session_id=session_id,
        token=token,
    )

    db.add(new_session)
    await db.commit()

    return {
        "session_id": session_id,
        "token": token,
    }

