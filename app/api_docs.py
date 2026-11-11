import json
from typing import Any, Dict, List, Optional

from fastapi.openapi.docs import swagger_ui_default_parameters
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

APP_DESCRIPTION = """
TrendPilot reads a signed-in Instagram Business or Creator account and turns long videos into short vertical clips for social media.

**Instagram:** open [/instagram/login](/instagram/login) in a new browser tab to sign in. Instagram sends you back to `/instagram/callback`, and after that `/instagram/me` works.

**Clips:** send a YouTube link or upload a video to `POST /clips/jobs`, then watch `GET /clips/jobs/{job_id}/events` until `status` is `done`. `GET /clips/jobs/{job_id}` returns the same job once. Each clip has a download `url`.

Every error response is `{ "error": "message" }`.
"""

SWAGGER_JS_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"
SWAGGER_CSS_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
SWAGGER_UI_PARAMETERS = {"tryItOutEnabled": True, "defaultModelsExpandDepth": 0}

# Swagger UI carries the multipart form state into the JSON editor when the body type is switched
# back to JSON, so the plugin refills the editor with that media type's example.
REFILL_JSON_EXAMPLE_PLUGIN = """
function refillJsonExample() {
  return {
    statePlugins: {
      oas3: {
        wrapActions: {
          setRequestContentType: (original, system) => (payload) => {
            const result = original(payload);
            const [path, method] = payload.pathMethod;
            const example = system.specSelectors
              .specJson()
              .getIn(["paths", path, method, "requestBody", "content", payload.value, "example"]);
            if (example && example.toJS) {
              system.oas3Actions.setRequestBodyValue({
                value: JSON.stringify(example.toJS(), null, 2),
                pathMethod: payload.pathMethod,
              });
            }
            return result;
          },
        },
      },
    },
  };
}
"""

OPENAPI_TAGS = [
    {"name": "Health", "description": "Check that the server is running."},
    {"name": "Instagram", "description": "Sign in with Instagram Business Login and read the signed-in account."},
    {"name": "Clips", "description": "Turn a video into vertical 9:16 clips with captions and suggested post text."},
]


class ErrorBody(BaseModel):
    error: str = Field(description="What went wrong.", examples=["Clip job not found."])


class InstagramCallbackBody(BaseModel):
    signedIn: bool = Field(examples=[True])
    userId: str = Field(description="Instagram user id of the signed-in account.", examples=["17841400000000000"])


class InstagramProfile(BaseModel):
    id: str = Field(examples=["17841400000000000"])
    username: Optional[str] = Field(default=None, examples=["trendpilot"])
    name: Optional[str] = Field(default=None, examples=["TrendPilot"])
    biography: Optional[str] = None
    website: Optional[str] = None
    followersCount: Optional[int] = Field(default=None, examples=[1250])
    followsCount: Optional[int] = Field(default=None, examples=[180])
    mediaCount: Optional[int] = Field(default=None, examples=[42])
    profilePictureUrl: Optional[str] = None


class InstagramMedia(BaseModel):
    id: str = Field(examples=["18000000000000000"])
    caption: Optional[str] = None
    mediaType: Optional[str] = Field(default=None, examples=["VIDEO"])
    mediaUrl: Optional[str] = None
    permalink: Optional[str] = None
    timestamp: Optional[str] = Field(default=None, examples=["2026-11-01T10:00:00+0000"])
    likeCount: Optional[int] = None
    commentsCount: Optional[int] = None


class InstagramAccountBody(BaseModel):
    profile: InstagramProfile
    media: List[InstagramMedia] = Field(description="The first page of media, up to 25 items.")
    nextCursor: Optional[str] = Field(default=None, description="Cursor for the next page, or null on the last page.")


class ClipJobCreated(BaseModel):
    jobId: str = Field(examples=["77df41b5fba046febd14291e1094aa18"])


class ClipBody(BaseModel):
    index: int = Field(description="1-based clip number, used in the download url.")
    start: float = Field(description="Start in seconds within the source video.")
    end: float = Field(description="End in seconds within the source video.")
    duration: float
    hook: str = Field(description="The opening line or visual that grabs attention.")
    title: str = Field(description="Short on-screen title.")
    caption: str = Field(description="Suggested social media caption.")
    hashtags: List[str] = Field(description="Suggested hashtags without the # sign.")
    score: int = Field(description="1 to 100, how likely Gemini thinks the clip is to go viral.")
    url: str = Field(description="Download path for the MP4.")


class ClipJobBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "jobId": "77df41b5fba046febd14291e1094aa18",
                "status": "done",
                "progress": 1.0,
                "error": None,
                "clips": [
                    {
                        "index": 1,
                        "start": 0.0,
                        "end": 16.72,
                        "duration": 16.72,
                        "hook": "Here is the one productivity trick nobody talks about.",
                        "title": "Stop checking email first",
                        "caption": "One week of doing my hardest task first doubled my output.",
                        "hashtags": ["productivity", "focus", "morningroutine"],
                        "score": 91,
                        "url": "/clips/jobs/77df41b5fba046febd14291e1094aa18/clips/1",
                    }
                ],
            }
        }
    )

    jobId: str
    status: str = Field(
        description="queued, downloading, transcribing, selecting, rendering, then done or failed."
    )
    progress: float = Field(description="0 to 1.")
    error: Optional[str] = Field(default=None, description="Why the job failed, when status is failed.")
    clips: List[ClipBody] = Field(description="Clips rendered so far. Complete when status is done.")


def swagger_ui_html(openapi_url: str, title: str) -> HTMLResponse:
    parameters = {**swagger_ui_default_parameters, **SWAGGER_UI_PARAMETERS, "url": openapi_url}
    return HTMLResponse(
        f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link type="text/css" rel="stylesheet" href="{SWAGGER_CSS_URL}">
<title>{title} - Swagger UI</title>
</head>
<body>
<div id="swagger-ui"></div>
<script src="{SWAGGER_JS_URL}"></script>
<script>
{REFILL_JSON_EXAMPLE_PLUGIN}
const ui = SwaggerUIBundle({{
  ...{json.dumps(parameters)},
  presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
  plugins: [refillJsonExample],
}});
</script>
</body>
</html>"""
    )


def error_responses(*codes: int) -> Dict[int, Dict[str, Any]]:
    descriptions = {
        400: "Bad request",
        401: "Not signed in",
        403: "Forbidden",
        404: "Not found",
        413: "Upload too large",
        415: "Unsupported content type",
        500: "Server is not configured",
        502: "Instagram request failed",
    }
    return {code: {"model": ErrorBody, "description": descriptions[code]} for code in codes}


CLIP_JOB_REQUEST_BODY: Dict[str, Any] = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["url"],
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "YouTube link (youtube.com or youtu.be).",
                        }
                    },
                },
                "example": {"url": "https://www.youtube.com/watch?v=VIDEO_ID"},
            },
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "required": ["file"],
                    "properties": {
                        "file": {
                            "type": "string",
                            "format": "binary",
                            "description": "Video file: .mp4, .mov, .m4v, .mkv, or .webm.",
                        }
                    },
                }
            },
        },
    }
}
