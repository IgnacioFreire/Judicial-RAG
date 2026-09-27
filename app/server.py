"""HTTP API and static UI. Replaces the Streamlit script."""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.schema_drafts import QuestionDraft, SchemaBuildError, build_schema
from app.ui_state import UiState, get_or_create_ui, reset_run_fields
from config.chunkers import CHUNK_TIERS
from config.embeddings import EMBEDDING_TIERS
from config.parsers import PARSER_TIERS
from models.query import DocumentAnswers
from pipeline.orchestrator import ProgressEvent, Stage, run
from storage.cleanup import cleanup_expired_sessions
from storage.session_manager import get_or_create_session
from storage.uploads import MAX_BYTES, MAX_MB, store_uploads

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

    queue: asyncio.Queue[RunEvent] = asyncio.Queue()

    def on_progress(event: ProgressEvent) -> None:
        if event.stage == Stage.ERROR:
            state.run_errors.append(event.message)
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
            await queue.put(
                RunEvent(
                    type="failed", stage=Stage.ERROR.value, message=state.pipeline_error
                )
            )
        finally:
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
