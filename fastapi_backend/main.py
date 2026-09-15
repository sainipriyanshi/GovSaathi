import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    status,
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

bearer_scheme = HTTPBearer(auto_error=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

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
    request: ChatRequest,
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
            ChatSession.session_id == request.session_id,
            ChatSession.token == credentials.credentials,
        )
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session or token",
        )

    answer = (
        "This is a mocked GovSaathi answer. "
        "The real RAG pipeline will be connected later."
    )

    citations = [
        {
            "title": "Government Scheme Knowledge Base",
            "source": "Django admin entries",
            "page": None,
        }
    ]

    created_at = datetime.now(timezone.utc)

    user_message = ChatMessage(
        session_id=request.session_id,
        role="user",
        content=request.query,
        detected_language=request.language,
        created_at=created_at,
    )

    assistant_message = ChatMessage(
        session_id=request.session_id,
        role="assistant",
        content=answer,
        citations_json=json.dumps(citations),
        detected_language=request.language,
        created_at=created_at,
    )

    db.add_all([user_message, assistant_message])
    await db.commit()

    return {
        "session_id": request.session_id,
        "query": request.query,
        "answer": answer,
        "citations": citations,
        "detected_language": request.language,
        "created_at": created_at,
    }


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

