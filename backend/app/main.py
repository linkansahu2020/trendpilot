import asyncio
import json
import shutil
from queue import Empty
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, Path, Query, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from starlette.datastructures import UploadFile

from app.api_docs import (
    APP_DESCRIPTION,
    CLIP_JOB_REQUEST_BODY,
    OPENAPI_TAGS,
    ClipJobBody,
    ClipJobCreated,
    InstagramAccountBody,
    InstagramCallbackBody,
    error_responses,
    swagger_ui_html,
)
from app.clipping.jobs import JOB_REMOVED, ClipJob, ClipJobStore
from app.clipping.pipeline import run_job
from app.clipping.settings import (
    load_clip_settings,
    missing_clip_configuration_message,
    missing_url_configuration_message,
)
from app.clipping.source import is_youtube_url, save_upload
from app.clipping.tools import ClipFailure
from app.instagram import (
    InstagramFailure,
    build_authorize_url,
    exchange_code,
    get_account,
    load_settings,
    missing_configuration_message,
)
from app.session import InstagramSessionStore

app = FastAPI(
    title="TrendPilot.Backend",
    version="0.1.0",
    description=APP_DESCRIPTION,
    openapi_tags=OPENAPI_TAGS,
    docs_url=None,
)
sessions = InstagramSessionStore()
clip_jobs = ClipJobStore()

JOB_ID = Path(description="The jobId returned by POST /clips/jobs.")


def error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status_code)


@app.get("/docs", include_in_schema=False)
def docs() -> HTMLResponse:
    return swagger_ui_html(app.openapi_url, app.title)


@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
    description="Returns the plain text `Hello World!` when the server is running.",
    response_class=PlainTextResponse,
    responses={200: {"content": {"text/plain": {"example": "Hello World!"}}}},
)
def root() -> PlainTextResponse:
    return PlainTextResponse("Hello World!")


@app.get(
    "/instagram/login",
    response_model=None,
    tags=["Instagram"],
    summary="Start Instagram sign-in",
    description=(
        "Stores a one-time `state` and redirects to Instagram Business Login with scope `instagram_business_basic`.\n\n"
        "Open [/instagram/login](/instagram/login) in a new browser tab. The Try it out button cannot follow "
        "an OAuth redirect to another site."
    ),
    status_code=302,
    responses={302: {"description": "Redirect to the Instagram authorize page."}, **error_responses(500)},
)
def instagram_login():
    settings = load_settings()
    missing = missing_configuration_message(settings)
    if missing is not None:
        return error_response(missing, 500)
    state = sessions.create_state()
    return RedirectResponse(build_authorize_url(settings, state), status_code=302)


@app.get(
    "/instagram/callback",
    response_model=None,
    tags=["Instagram"],
    summary="Instagram sign-in callback",
    description=(
        "Instagram redirects the browser here after sign-in; you do not call it yourself. It checks `state`, "
        "exchanges `code` for a short-lived token and then a 60-day token, and stores the login in memory."
    ),
    responses={200: {"model": InstagramCallbackBody}, **error_responses(400, 403, 500, 502)},
)
async def instagram_callback(
    code: Optional[str] = Query(None, description="Authorization code from Instagram. A trailing `#_` is removed."),
    state: Optional[str] = Query(None, description="The one-time state created by /instagram/login."),
    error: Optional[str] = Query(None, description="Set by Instagram when the user cancels or sign-in fails."),
    error_description: Optional[str] = Query(None, description="Instagram's explanation of `error`."),
) -> JSONResponse:
    if error is not None and error.strip():
        message = error_description if error_description and error_description.strip() else error
        return JSONResponse({"error": message}, status_code=400)

    settings = load_settings()
    missing = missing_configuration_message(settings)
    if missing is not None:
        return JSONResponse({"error": missing}, status_code=500)

    if state is None or not state.strip() or not sessions.try_consume_state(state):
        return JSONResponse(
            {"error": "The Instagram login state is missing or expired. Start again at /instagram/login."},
            status_code=400,
        )

    if code is None or not code.strip():
        return JSONResponse({"error": "Instagram did not return an authorization code."}, status_code=400)

    login = await exchange_code(settings, code)
    if isinstance(login, InstagramFailure):
        return JSONResponse({"error": login.message}, status_code=login.status_code)

    sessions.set_login(login)
    return JSONResponse({"signedIn": True, "userId": login.user_id})


@app.get(
    "/instagram/me",
    response_model=None,
    tags=["Instagram"],
    summary="Get the signed-in account",
    description="Returns the signed-in profile and the first page of media. Sign in at /instagram/login first.",
    responses={200: {"model": InstagramAccountBody}, **error_responses(401, 403, 502)},
)
async def instagram_me() -> JSONResponse:
    session = sessions.get_valid()
    if session is None:
        return JSONResponse({"error": "Sign in at /instagram/login."}, status_code=401)

    account = await get_account(load_settings(), session.user_id, session.access_token)
    if isinstance(account, InstagramFailure):
        return JSONResponse({"error": account.message}, status_code=account.status_code)
    return JSONResponse(account)


@app.post(
    "/clips/jobs",
    response_model=None,
    tags=["Clips"],
    summary="Start a clip job",
    description=(
        "Send **one** of:\n\n"
        "- `multipart/form-data` with a `file` field holding a .mp4, .mov, .m4v, .mkv, or .webm video.\n"
        "- `application/json` with `{ \"url\": \"https://www.youtube.com/watch?v=...\" }`. "
        "Only youtube.com and youtu.be links are accepted, and only when `Clips__AllowUrls` is on. "
        "Links need a standalone yt-dlp: `brew install yt-dlp`, which also installs deno.\n\n"
        "Uploads are limited by `Clips__MaxUploadMb` and videos by `Clips__MaxDurationMinutes`. "
        "The job runs in the background. Watch it at `GET /clips/jobs/{job_id}/events`, "
        "or read it once at `GET /clips/jobs/{job_id}`."
    ),
    status_code=202,
    openapi_extra=CLIP_JOB_REQUEST_BODY,
    responses={202: {"model": ClipJobCreated}, **error_responses(400, 403, 413, 415, 500)},
)
async def create_clip_job(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    settings = load_clip_settings()
    missing = missing_clip_configuration_message(settings)
    if missing is not None:
        return error_response(missing, 500)

    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        content_length = request.headers.get("content-length", "")
        if content_length.isdigit() and int(content_length) > settings.max_upload_bytes + 1024 * 1024:
            return error_response(f"The upload is larger than {settings.max_upload_bytes // (1024 * 1024)} MB.", 413)
        form = await request.form()
        upload = form.get("file")
        if not isinstance(upload, UploadFile):
            return error_response("Send the video in a multipart field named file.", 400)
        job = clip_jobs.create(settings.work_dir)
        saved = await save_upload(upload, job.work_dir, settings.max_upload_bytes)
        await upload.close()
        if isinstance(saved, ClipFailure):
            remove_job(job.id)
            return error_response(saved.message, 400)
        background_tasks.add_task(run_job, clip_jobs, job.id, settings, None, saved)
        return JSONResponse({"jobId": job.id}, status_code=202)

    if content_type.startswith("application/json"):
        if not settings.allow_urls:
            return error_response("YouTube links are turned off. Upload the video file instead.", 403)
        missing_url_tool = missing_url_configuration_message(settings)
        if missing_url_tool is not None:
            return error_response(missing_url_tool, 500)
        try:
            body = await request.json()
        except ValueError:
            return error_response("The request body is not valid JSON.", 400)
        url = body.get("url") if isinstance(body, dict) else None
        if not isinstance(url, str) or not is_youtube_url(url):
            return error_response("Send a YouTube link as { \"url\": \"https://www.youtube.com/watch?v=...\" }.", 400)
        job = clip_jobs.create(settings.work_dir)
        background_tasks.add_task(run_job, clip_jobs, job.id, settings, url.strip(), None)
        return JSONResponse({"jobId": job.id}, status_code=202)

    return error_response("Send JSON with a YouTube url or a multipart upload with a file field.", 415)


@app.get(
    "/clips/jobs/{job_id}",
    response_model=None,
    tags=["Clips"],
    summary="Get clip job status",
    description=(
        "Status moves through `queued`, `downloading`, `transcribing`, `selecting`, and `rendering`, "
        "then ends at `done` or `failed`. When it fails, `error` says why. "
        "`GET /clips/jobs/{job_id}/events` sends this same body again each time it changes. "
        "Jobs are kept in memory and are forgotten when the server restarts."
    ),
    responses={200: {"model": ClipJobBody}, **error_responses(404)},
)
def get_clip_job(job_id: str = JOB_ID) -> JSONResponse:
    job = clip_jobs.get(job_id)
    if job is None:
        return error_response("Clip job not found.", 404)
    return JSONResponse(read_clip_job(job))


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


async def _clip_job_event_stream(request: Request, job_id: str):
    subscription = clip_jobs.subscribe(job_id)
    if subscription is None:
        yield _sse({"error": "Clip job not found."})
        return
    listener, job = subscription.listener, subscription.job
    try:
        yield _sse(read_clip_job(job))
        while job.status not in {"done", "failed"}:
            try:
                item = await asyncio.to_thread(listener.get, True, 15)
            except Empty:
                yield ": keep-alive\n\n"
                if await request.is_disconnected():
                    return
                continue
            if item is JOB_REMOVED:
                yield _sse({"error": "Clip job not found."})
                return
            job = item
            yield _sse(read_clip_job(job))
    finally:
        clip_jobs.unsubscribe(job_id, listener)


@app.get(
    "/clips/jobs/{job_id}/events",
    response_model=None,
    tags=["Clips"],
    summary="Watch a clip job",
    description=(
        "Holds the response open and sends the job JSON again each time the status or clip list changes. "
        "Each `data:` line is the same object as `GET /clips/jobs/{job_id}`. "
        "The first event is the job as it is now. The stream ends after `done` or `failed`. "
        "A comment line (`: keep-alive`) is sent every 15 seconds while the job is still running. "
        "If the job is deleted after the stream has started, the last event is `{ \"error\": \"Clip job not found.\" }`."
    ),
    responses={
        200: {"content": {"text/event-stream": {"schema": {"type": "string"}}}},
        **error_responses(404),
    },
)
async def watch_clip_job(request: Request, job_id: str = JOB_ID):
    if clip_jobs.get(job_id) is None:
        return error_response("Clip job not found.", 404)
    return StreamingResponse(
        _clip_job_event_stream(request, job_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get(
    "/clips/jobs/{job_id}/clips/{index}",
    response_model=None,
    tags=["Clips"],
    summary="Download a clip",
    description="Returns the rendered 1080x1920 MP4 with burned-in captions.",
    responses={
        200: {"description": "The clip video.", "content": {"video/mp4": {"schema": {"type": "string", "format": "binary"}}}},
        **error_responses(404),
    },
)
def get_clip_file(
    job_id: str = JOB_ID,
    index: int = Path(description="The clip's `index` from the job status."),
):
    job = clip_jobs.get(job_id)
    if job is None:
        return error_response("Clip job not found.", 404)
    clip = next((item for item in job.clips if item.index == index), None)
    if clip is None or not clip.path.is_file():
        return error_response("Clip not found.", 404)
    return FileResponse(clip.path, media_type="video/mp4", filename=f"clip-{index}.mp4")


@app.delete(
    "/clips/jobs/{job_id}",
    response_model=None,
    tags=["Clips"],
    summary="Delete a clip job",
    description="Forgets the job and deletes its folder, including every rendered clip.",
    status_code=204,
    responses={204: {"description": "Deleted."}, **error_responses(404)},
)
def delete_clip_job(job_id: str = JOB_ID):
    if not remove_job(job_id):
        return error_response("Clip job not found.", 404)
    return Response(status_code=204)


def remove_job(job_id: str) -> bool:
    job = clip_jobs.remove(job_id)
    if job is None:
        return False
    shutil.rmtree(job.work_dir, ignore_errors=True)
    return True


def read_clip_job(job: ClipJob) -> dict:
    return {
        "jobId": job.id,
        "status": job.status,
        "progress": round(job.progress, 2),
        "error": job.error,
        "clips": [
            {
                "index": clip.index,
                "start": clip.start,
                "end": clip.end,
                "duration": round(clip.duration, 2),
                "hook": clip.hook,
                "title": clip.title,
                "caption": clip.caption,
                "hashtags": clip.hashtags,
                "score": clip.score,
                "url": f"/clips/jobs/{job.id}/clips/{clip.index}",
            }
            for clip in job.clips
        ],
    }
