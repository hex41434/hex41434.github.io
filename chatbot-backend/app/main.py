import json
import os
import re
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:8000,http://127.0.0.1:8000,"
    "http://localhost:8080,http://127.0.0.1:8080,"
    "https://hex41434.github.io"
)
KNOWLEDGE_PATH = Path(os.getenv("KNOWLEDGE_PATH", "/site-data/aida-chatbot-knowledge.json"))
if not KNOWLEDGE_PATH.exists():
    KNOWLEDGE_PATH = Path(__file__).resolve().parents[2] / "hex41434.github.io" / "data" / "aida-chatbot-knowledge.json"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "12"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "45"))
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "1200"))
MAX_REQUEST_BYTES = int(os.getenv("MAX_REQUEST_BYTES", "4096"))

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9+#.]+")
STOPWORDS = {
    "a", "about", "an", "and", "are", "as", "at", "be", "by", "can", "for", "from",
    "has", "have", "her", "how", "i", "in", "is", "it", "me", "of", "on", "or",
    "she", "that", "the", "this", "to", "what", "where", "with", "you", "your"
}
TOKEN_ALIASES = {
    "bsc": {"bachelor", "bachelors", "degree", "education"},
    "bachelor": {"bsc", "bachelors", "degree", "education"},
    "bachelors": {"bsc", "bachelor", "degree", "education"},
    "doctorate": {"phd", "degree", "education"},
    "master": {"msc", "masters", "degree", "education"},
    "masters": {"msc", "master", "degree", "education"},
    "msc": {"master", "masters", "degree", "education"},
    "phd": {"doctorate", "degree", "education"},
}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


def parse_allowed_origins() -> list[str]:
    origins = os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


def load_knowledge() -> list[dict[str, str]]:
    try:
        data = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Knowledge file not found: {KNOWLEDGE_PATH}") from exc

    chunks = data.get("chunks", [])
    if not isinstance(chunks, list) or not chunks:
        raise RuntimeError("Knowledge file must contain a non-empty 'chunks' list")
    return chunks


KNOWLEDGE_CHUNKS = load_knowledge()
app = FastAPI(title="Aida Website Chatbot API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_allowed_origins(),
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type"],
)

request_log: dict[str, deque[float]] = defaultdict(deque)


def normalize_token(token: str) -> str:
    return token.lower().replace(".", "").strip()


def tokenize(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw_token in TOKEN_PATTERN.findall(text):
        token = normalize_token(raw_token)
        if len(token) <= 1 or token in STOPWORDS:
            continue

        tokens.add(token)
        tokens.update(TOKEN_ALIASES.get(token, set()))
    return tokens


def retrieve_chunks(message: str, limit: int = 5) -> list[dict[str, str]]:
    query_tokens = tokenize(message)
    if not query_tokens:
        return KNOWLEDGE_CHUNKS[:limit]

    scored_chunks: list[tuple[int, dict[str, str]]] = []
    for chunk in KNOWLEDGE_CHUNKS:
        haystack = " ".join([chunk.get("title", ""), chunk.get("text", ""), chunk.get("id", "")])
        chunk_tokens = tokenize(haystack)
        score = len(query_tokens.intersection(chunk_tokens))
        if score:
            scored_chunks.append((score, chunk))

    if not scored_chunks:
        return KNOWLEDGE_CHUNKS[:3]

    scored_chunks.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored_chunks[:limit]]


def client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(ip_address: str) -> None:
    now = time.monotonic()
    window_start = now - 60
    hits = request_log[ip_address]

    while hits and hits[0] < window_start:
        hits.popleft()

    if len(hits) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again soon.")

    hits.append(now)


def build_messages(user_message: str, chunks: list[dict[str, str]]) -> list[dict[str, str]]:
    context = "\n\n".join(
        f"[{chunk.get('id', 'unknown')}] {chunk.get('title', 'Untitled')}\n{chunk.get('text', '')}"
        for chunk in chunks
    )
    system_prompt = (
        "You are the public website assistant for Aida Farahani. "
        "Answer only about Aida Farahani's profile, CV, projects, research, skills, education, contact, and website content. "
        "Use only the supplied context. If the answer is not present in the context, say that the website does not include that information. "
        "Do not invent employment history, credentials, publications, phone numbers, or project claims. "
        "Do not mention a contact form. The website does not list one. "
        "For contact questions, provide only the public contact options from the context. "
        "Do not include contact details unless the visitor asks for contact information. "
        "Keep answers concise, helpful, and factual."
    )
    user_prompt = f"Context:\n{context}\n\nVisitor question: {user_message}"
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


async def ask_ollama(messages: list[dict[str, str]]) -> str:
    payload: dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 320,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail="The local model server is unavailable. Please try again later.",
        ) from exc

    data = response.json()
    answer = data.get("message", {}).get("content", "").strip()
    if not answer:
        raise HTTPException(status_code=502, detail="The local model returned an empty answer.")
    return answer


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "model": OLLAMA_MODEL}


@app.middleware("http")
async def limit_request_size(request: Request, call_next: Any) -> Any:
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Request body is too large."})
    return await call_next(request)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    enforce_rate_limit(client_ip(request))
    user_message = payload.message.strip()
    chunks = retrieve_chunks(user_message)
    messages = build_messages(user_message, chunks)
    answer = await ask_ollama(messages)
    return ChatResponse(answer=answer, sources=[chunk.get("id", "unknown") for chunk in chunks])
