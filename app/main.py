from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse

from app.instagram import (
    InstagramFailure,
    build_authorize_url,
    exchange_code,
    get_account,
    load_settings,
    missing_configuration_message,
)
from app.session import InstagramSessionStore

app = FastAPI(title="TrendPilot.Backend")
sessions = InstagramSessionStore()


def error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status_code)


@app.get("/")
def root() -> PlainTextResponse:
    return PlainTextResponse("Hello World!")


@app.get("/instagram/login", response_model=None)
def instagram_login():
    settings = load_settings()
    missing = missing_configuration_message(settings)
    if missing is not None:
        return error_response(missing, 500)
    state = sessions.create_state()
    return RedirectResponse(build_authorize_url(settings, state), status_code=302)


@app.get("/instagram/callback")
async def instagram_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
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


@app.get("/instagram/me")
async def instagram_me() -> JSONResponse:
    session = sessions.get_valid()
    if session is None:
        return JSONResponse({"error": "Sign in at /instagram/login."}, status_code=401)

    account = await get_account(load_settings(), session.user_id, session.access_token)
    if isinstance(account, InstagramFailure):
        return JSONResponse({"error": account.message}, status_code=account.status_code)
    return JSONResponse(account)
