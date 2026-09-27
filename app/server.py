"""HTTP API and static UI. Replaces the Streamlit script."""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.schema_drafts import QuestionDraft, SchemaBuildError, build_schema
from app.ui_state import (
    UiState,
    close_run,
    drop_ui,
    get_or_create_ui,
    mark_queued,
    note_progress,
    reset_run_fields,
    sync_accepted,
)
from config.chunkers import CHUNK_TIERS
from config.embeddings import EMBEDDING_TIERS
from config.parsers import PARSER_TIERS
from config.settings import settings
from models.query import DocumentAnswers
from pipeline.embedder import reset_inference_client
from pipeline.orchestrator import ProgressEvent, Stage, run
from services.llm_usage import bind as bind_usage
from services.llm_usage import clear, totals
from services.llm_usage import unbind as unbind_usage
from services.session_secrets import (
    active_llm_key_configured,
    huggingface_key_configured,
)
from services.session_secrets import (
    bind as bind_secrets,
)
from services.session_secrets import (
    unbind as unbind_secrets,
)
from storage.cleanup import cleanup_expired_sessions, cleanup_session
from storage.session_manager import get_or_create_session
from storage.uploads import MAX_BYTES, MAX_MB, file_name, store_uploads

logger = logging.getLogger(__name__)

COOKIE = "jr_session"
_TIER_WORDS = {"fast": "Fast", "medium": "Medium", "slow": "Slow"}
_WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"
_NOISY_LOGGERS = (
    "docling",
    "transformers",
    "huggingface_hub",
    "rapidocr",
    "httpx",
    "supabase",
    "postgrest",
    "gotrue",
)


class TierOption(BaseModel):
    value: str
    label: str


class SessionView(BaseModel):
    parser_tier: str
    chunk_tier: str
    embedding_tier: str
    parser_options: list[TierOption]
    chunk_options: list[TierOption]
    embedding_options: list[TierOption]
    accepted_files: list[str]
    schema_saved: bool
    question_count: int = 0
    is_processing: bool
    run_errors: list[str]
    pipeline_error: str | None = None
    success_message: str | None = None
    results: list[DocumentAnswers] | None = None
    max_upload_mb: int = MAX_MB


class RejectedFile(BaseModel):
    name: str
    detail: str


class UploadView(BaseModel):
    accepted_files: list[str]
    rejected: list[RejectedFile]


class SchemaSaveView(BaseModel):
    saved: bool
    question_count: int = 0
    error: SchemaBuildError | None = None


class TierPatch(BaseModel):
    parser_tier: str | None = None
    chunk_tier: str | None = None
    embedding_tier: str | None = None


class ProfileView(BaseModel):
    email: str
    llm_provider: str
    llm_model: str
    llm_key_configured: bool
    embedding_provider: str
    embedding_model: str
    huggingface_key_configured: bool
    input_tokens: int
    output_tokens: int


class KeysPatch(BaseModel):
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    deepseek_api_key: str | None = None
    huggingface_api_key: str | None = None


class KeysView(BaseModel):
    llm_key_configured: bool
    huggingface_key_configured: bool
    llm_env_var: str
    llm_key_field: str
    huggingface_env_var: str = "HUGGINGFACE_API_KEY"


class SignOutView(BaseModel):
    signed_out: bool = True


class DocumentListItem(BaseModel):
    name: str
    status: str
    accepted_at: str
    started_at: str | None = None
    finished_at: str | None = None


class DocumentDetail(BaseModel):
    name: str
    status: str
    accepted_at: str
    started_at: str | None = None
    finished_at: str | None = None
    answers: DocumentAnswers | None = None


class RunEvent(BaseModel):
    type: Literal["progress", "done", "failed"]
    stage: str = ""
    source: str = ""
    message: str = ""
    current: int = 0
    total: int = 0
    results: list[DocumentAnswers] | None = None


def _tier_options(mapping: dict[str, str]) -> list[TierOption]:
    return [
        TierOption(value=tier, label=f"{_TIER_WORDS[tier]} — {method}")
        for tier, method in mapping.items()
    ]


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _configure_logging()
    yield


app = FastAPI(title="Judicial RAG", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _bind(request: Request) -> tuple[str, bool]:
    cleanup_expired_sessions()
    existing = request.cookies.get(COOKIE)
    if existing:
        get_or_create_session(existing)
        return existing, False
    session_id = str(uuid.uuid4())
    get_or_create_session(session_id)
    return session_id, True


def _set_cookie(response: Response, session_id: str, is_new: bool) -> None:
    if is_new:
        response.set_cookie(
            COOKIE,
            session_id,
            httponly=True,
            samesite="lax",
            path="/",
        )


def _json(model: BaseModel, session_id: str, is_new: bool) -> JSONResponse:
    response = JSONResponse(model.model_dump(mode="json"))
    _set_cookie(response, session_id, is_new)
    return response


def _paths_for(session_id: str) -> list[Path]:
    session = get_or_create_session(session_id)
    return [path for path in session.pdf_dir.iterdir() if path.is_file()]


def _file_names(session_id: str) -> list[str]:
    return [path.name for path in _paths_for(session_id)]


def _view(session_id: str, state: UiState) -> SessionView:
    schema = state.schema
    return SessionView(
        parser_tier=state.parser_tier,
        chunk_tier=state.chunk_tier,
        embedding_tier=state.embedding_tier,
        parser_options=_tier_options(PARSER_TIERS),
        chunk_options=_tier_options(CHUNK_TIERS),
        embedding_options=_tier_options(EMBEDDING_TIERS),
        accepted_files=_file_names(session_id),
        schema_saved=schema is not None,
        question_count=len(schema.questions) if schema else 0,
        is_processing=state.is_processing,
        run_errors=list(state.run_errors),
        pipeline_error=state.pipeline_error,
        success_message=state.success_message,
        results=state.results,
    )


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _row_item(row) -> DocumentListItem:
    return DocumentListItem(
        name=row.name,
        status=row.status,
        accepted_at=row.accepted_at.isoformat(),
        started_at=_iso(row.started_at),
        finished_at=_iso(row.finished_at),
    )


def _llm_env_var() -> str:
    names = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }
    return names[settings.llm_provider]


def _llm_key_field() -> str:
    fields = {
        "anthropic": "anthropic_api_key",
        "openai": "openai_api_key",
        "gemini": "gemini_api_key",
        "deepseek": "deepseek_api_key",
    }
    return fields[settings.llm_provider]


def _profile_for(session_id: str, state: UiState) -> ProfileView:
    overrides = state.key_overrides
    input_tokens, output_tokens = totals(session_id)
    return ProfileView(
        email=settings.supabase_admin_email,
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        llm_key_configured=active_llm_key_configured(overrides),
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.embedding_model,
        huggingface_key_configured=huggingface_key_configured(overrides),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


@app.get("/api/session")
def get_session(request: Request) -> JSONResponse:
    session_id, is_new = _bind(request)
    return _json(_view(session_id, get_or_create_ui(session_id)), session_id, is_new)


@app.put("/api/uploads")
async def put_uploads(
    request: Request,
    files: Annotated[list[UploadFile] | None, File()] = None,
) -> JSONResponse:
    session_id, is_new = _bind(request)
    state = get_or_create_ui(session_id)
    if state.is_processing:
        raise HTTPException(status_code=409, detail="A run is in progress.")
    session = get_or_create_session(session_id)
    accepted: list[tuple[str, bytes]] = []
    rejected: list[RejectedFile] = []
    for upload in files or []:
        data = await upload.read()
        name = upload.filename or "upload.pdf"
        if len(data) > MAX_BYTES:
            size_mb = len(data) / (1024 * 1024)
            rejected.append(
                RejectedFile(
                    name=name,
                    detail=f"{name} ({size_mb:.1f} MB — limit {MAX_MB} MB)",
                )
            )
            logger.warning("Rejected oversized file: %s (%d bytes)", name, len(data))
            continue
        accepted.append((name, data))
    paths = store_uploads(session.pdf_dir, accepted)
    sync_accepted(state, [path.name for path in paths])
    return _json(
        UploadView(
            accepted_files=[path.name for path in paths],
            rejected=rejected,
        ),
        session_id,
        is_new,
    )


@app.put("/api/schema")
def put_schema(request: Request, drafts: list[QuestionDraft]) -> JSONResponse:
    session_id, is_new = _bind(request)
    state = get_or_create_ui(session_id)
    if state.is_processing:
        raise HTTPException(status_code=409, detail="A run is in progress.")
    schema, error = build_schema(drafts)
    if schema is None:
        return _json(SchemaSaveView(saved=False, error=error), session_id, is_new)
    state.schema = schema
    logger.info("Schema saved: %d questions", len(schema.questions))
    return _json(
        SchemaSaveView(saved=True, question_count=len(schema.questions)),
        session_id,
        is_new,
    )


@app.patch("/api/session/tiers")
def patch_tiers(request: Request, body: TierPatch) -> JSONResponse:
    session_id, is_new = _bind(request)
    state = get_or_create_ui(session_id)
    if state.is_processing:
        raise HTTPException(status_code=409, detail="A run is in progress.")
    if body.parser_tier is not None:
        if body.parser_tier not in PARSER_TIERS:
            raise HTTPException(status_code=400, detail="Unknown parser tier.")
        state.parser_tier = body.parser_tier
    if body.chunk_tier is not None:
        if body.chunk_tier not in CHUNK_TIERS:
            raise HTTPException(status_code=400, detail="Unknown chunk tier.")
        state.chunk_tier = body.chunk_tier
    if body.embedding_tier is not None:
        if body.embedding_tier not in EMBEDDING_TIERS:
            raise HTTPException(status_code=400, detail="Unknown retrieval tier.")
        state.embedding_tier = body.embedding_tier
    return _json(_view(session_id, state), session_id, is_new)


@app.post("/api/reset")
def post_reset(request: Request) -> JSONResponse:
    session_id, is_new = _bind(request)
    state = get_or_create_ui(session_id)
    if state.is_processing:
        raise HTTPException(status_code=409, detail="A run is in progress.")
    session = get_or_create_session(session_id)
    store_uploads(session.pdf_dir, [])
    reset_run_fields(state)
    clear(session_id)
    return _json(_view(session_id, state), session_id, is_new)


@app.post("/api/run")
async def post_run(request: Request) -> StreamingResponse:
    session_id, is_new = _bind(request)
    state = get_or_create_ui(session_id)
    if state.is_processing:
        raise HTTPException(status_code=409, detail="A run is in progress.")
    pdf_paths = _paths_for(session_id)
    if not pdf_paths or state.schema is None:
        raise HTTPException(
            status_code=400,
            detail="Upload PDFs and save a schema first.",
        )
    state.is_processing = True
    state.results = None
    state.run_errors = []
    state.pipeline_error = None
    state.success_message = None
    schema = state.schema
    parser_tier = state.parser_tier
    chunk_tier = state.chunk_tier
    embedding_tier = state.embedding_tier
    mark_queued(state, [path.name for path in pdf_paths])

    queue: asyncio.Queue[RunEvent] = asyncio.Queue()

    def on_progress(event: ProgressEvent) -> None:
        if event.stage == Stage.ERROR:
            state.run_errors.append(event.message)
        note_progress(state, event.stage.value, event.source)
        queue.put_nowait(
            RunEvent(
                type="progress",
                stage=event.stage.value,
                source=event.source,
                message=event.message,
                current=event.current,
                total=event.total,
            )
        )

    async def work() -> None:
        usage_token = bind_usage(session_id)
        secrets_token = bind_secrets(state.key_overrides)
        try:
            results = await run(
                pdf_paths=pdf_paths,
                schema=schema,
                session_id=session_id,
                on_progress=on_progress,
                parser_tier=parser_tier,
                chunk_tier=chunk_tier,
                embedding_tier=embedding_tier,
            )
            state.results = results
            close_run(state, {item.document for item in results})
            state.success_message = f"Done — {len(results)} document(s) processed."
            logger.info("Pipeline complete: %d documents", len(results))
            await asyncio.sleep(0)
            await queue.put(
                RunEvent(
                    type="done",
                    stage=Stage.COMPLETE.value,
                    message=state.success_message,
                    current=1,
                    total=1,
                    results=results,
                )
            )
        except Exception as exc:
            logger.exception("Pipeline failed")
            state.pipeline_error = f"Pipeline failed: {exc}"
            close_run(state, set())
            await queue.put(
                RunEvent(
                    type="failed", stage=Stage.ERROR.value, message=state.pipeline_error
                )
            )
        finally:
            unbind_secrets(secrets_token)
            unbind_usage(usage_token)
            state.is_processing = False

    async def events() -> AsyncIterator[str]:
        task = asyncio.create_task(work())
        try:
            while True:
                event = await queue.get()
                yield f"data: {event.model_dump_json()}\n\n"
                if event.type in {"done", "failed"}:
                    break
        finally:
            await task

    stream = StreamingResponse(events(), media_type="text/event-stream")
    _set_cookie(stream, session_id, is_new)
    return stream


def _safe_name(name: str) -> str | None:
    cleaned = file_name(name)
    if not cleaned or cleaned in {".", ".."} or cleaned != name:
        return None
    return cleaned


@app.get("/api/documents")
def get_documents(request: Request) -> JSONResponse:
    session_id, is_new = _bind(request)
    state = get_or_create_ui(session_id)
    rows = [_row_item(row) for row in state.documents.values()]
    rows.sort(key=lambda row: row.accepted_at)
    return _json_list(rows, session_id, is_new)


@app.get("/api/documents/{name}")
def get_document(name: str, request: Request) -> JSONResponse:
    session_id, is_new = _bind(request)
    safe = _safe_name(name)
    state = get_or_create_ui(session_id)
    row = state.documents.get(safe) if safe else None
    if row is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    answers = None
    for doc in state.results or []:
        if doc.document == row.name:
            answers = doc
            break
    detail = DocumentDetail(
        name=row.name,
        status=row.status,
        accepted_at=row.accepted_at.isoformat(),
        started_at=_iso(row.started_at),
        finished_at=_iso(row.finished_at),
        answers=answers,
    )
    return _json(detail, session_id, is_new)


@app.get("/api/profile")
def get_profile(request: Request) -> JSONResponse:
    session_id, is_new = _bind(request)
    state = get_or_create_ui(session_id)
    return _json(_profile_for(session_id, state), session_id, is_new)


@app.get("/api/profile/keys")
def get_profile_keys(request: Request) -> JSONResponse:
    session_id, is_new = _bind(request)
    state = get_or_create_ui(session_id)
    overrides = state.key_overrides
    view = KeysView(
        llm_key_configured=active_llm_key_configured(overrides),
        huggingface_key_configured=huggingface_key_configured(overrides),
        llm_env_var=_llm_env_var(),
        llm_key_field=_llm_key_field(),
    )
    return _json(view, session_id, is_new)


@app.put("/api/profile/keys")
def put_profile_keys(request: Request, body: KeysPatch) -> JSONResponse:
    session_id, is_new = _bind(request)
    state = get_or_create_ui(session_id)
    if state.is_processing:
        raise HTTPException(status_code=409, detail="A run is in progress.")
    state.key_overrides.merge(body)
    reset_inference_client()
    overrides = state.key_overrides
    view = KeysView(
        llm_key_configured=active_llm_key_configured(overrides),
        huggingface_key_configured=huggingface_key_configured(overrides),
        llm_env_var=_llm_env_var(),
        llm_key_field=_llm_key_field(),
    )
    return _json(view, session_id, is_new)


@app.post("/api/sign-out")
def post_sign_out(request: Request) -> JSONResponse:
    session_id = request.cookies.get(COOKIE)
    if session_id:
        state = get_or_create_ui(session_id)
        if state.is_processing:
            raise HTTPException(status_code=409, detail="A run is in progress.")
        cleanup_session(session_id)
        drop_ui(session_id)
        clear(session_id)
    new_id = str(uuid.uuid4())
    get_or_create_session(new_id)
    response = _json(SignOutView(), new_id, True)
    response.delete_cookie(COOKIE, path="/")
    response.set_cookie(
        COOKIE,
        new_id,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return response


def _json_list(rows: list[BaseModel], session_id: str, is_new: bool) -> JSONResponse:
    response = JSONResponse([row.model_dump(mode="json") for row in rows])
    _set_cookie(response, session_id, is_new)
    return response


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if _WEB_DIST.is_dir():
    assets = _WEB_DIST / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/")
    def index_page() -> FileResponse:
        return FileResponse(_WEB_DIST / "index.html")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = _WEB_DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_WEB_DIST / "index.html")
else:

    @app.get("/")
    def missing_ui() -> JSONResponse:
        return JSONResponse(
            {
                "detail": "The React UI is not built. Run npm run build in web/, "
                "or npm run dev on port 5173."
            },
            status_code=503,
        )
