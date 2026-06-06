import threading
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config.config_manager import ConfigManager
from config.defaults import DEFAULT_PROMPT_TEMPLATE
from bootstrap import build_history, build_ai

# Everything for the front-end lives flat in this directory: index.html,
# styles.css, app.js. `/static` is mounted here so /static/styles.css resolves.
_UI_DIR = Path(__file__).parent
_INDEX = _UI_DIR / "index.html"


class ConfigPatch(BaseModel):
    ai: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    history: Optional[Dict[str, Any]] = None
    ui: Optional[Dict[str, Any]] = None


class KeyTest(BaseModel):
    api_key: Optional[str] = None  # when omitted, test the currently-resolved key


def _public_config(cfg: ConfigManager) -> Dict[str, Any]:
    """Config view for the browser, with the secret stripped to metadata."""
    data = cfg.all()
    raw_key = cfg.resolve_api_key()
    data.get("ai", {}).pop("api_key", None)
    data["ai"]["api_key_set"] = raw_key != ""
    data["ai"]["api_key_source"] = cfg.api_key_source()
    # Send a masked preview: first half visible, rest as dots
    if raw_key:
        half = len(raw_key) // 2
        data["ai"]["api_key_preview"] = raw_key[:half] + "•" * (len(raw_key) - half)
    else:
        data["ai"]["api_key_preview"] = ""
    return data


def create_app(cfg: Optional[ConfigManager] = None) -> FastAPI:
    """Build the FastAPI app. Accepts a ConfigManager for testability."""
    cfg = cfg or ConfigManager()
    app = FastAPI(title="Lazzy Commit Settings", docs_url=None, redoc_url=None)

    app.mount("/static", StaticFiles(directory=str(_UI_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return HTMLResponse(_INDEX.read_text(encoding="utf-8"))

    # ----- config ----------------------------------------------------------
    @app.get("/api/config")
    def get_config() -> JSONResponse:
        cfg.reload()
        return JSONResponse(_public_config(cfg))

    @app.get("/api/config/key")
    def get_config_key() -> JSONResponse:
        return JSONResponse({"api_key": cfg.resolve_api_key()})

    @app.put("/api/config")
    def update_config(patch: ConfigPatch) -> JSONResponse:
        body = {k: v for k, v in patch.model_dump().items() if v is not None}
        # Empty api_key string means "leave unchanged" so saving other settings
        # never wipes a key the user set earlier and didn't retype.
        if "ai" in body and body["ai"].get("api_key", None) == "":
            body["ai"].pop("api_key")
        try:
            cfg.update(body)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return JSONResponse(_public_config(cfg))

    @app.get("/api/defaults/prompt")
    def default_prompt() -> JSONResponse:
        return JSONResponse({"prompt_template": DEFAULT_PROMPT_TEMPLATE})

    @app.get("/api/models")
    def get_models(api_key: Optional[str] = None) -> JSONResponse:
        import urllib.request
        import json
        key = (api_key or "").strip() or cfg.resolve_api_key()

        if not key:
            return JSONResponse({"models": [], "source": "none", "error": "No API key configured"})

        try:
            req = urllib.request.Request(
                "https://generativelanguage.googleapis.com/v1beta/models",
                headers={
                    "x-goog-api-key": key,
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                res_data = json.loads(response.read().decode("utf-8"))

            api_models = []
            for m in res_data.get("models", []):
                supported_methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in supported_methods:
                    name = m.get("name", "")
                    if name.startswith("models/"):
                        name = name[7:]
                    api_models.append({
                        "name": name,
                        "display_name": m.get("displayName", name)
                    })
            return JSONResponse({"models": api_models, "source": "api"})
        except Exception as exc:
            print(f"Error fetching models from Gemini API: {exc}")
            return JSONResponse({"models": [], "source": "error", "error": str(exc)})

    # ----- key test --------------------------------------------------------
    @app.post("/api/test-key")
    def test_key(body: KeyTest) -> JSONResponse:
        key = (body.api_key or "").strip() or cfg.resolve_api_key()
        if not key:
            return JSONResponse({"ok": False, "message": "No API key provided"})
        try:
            ai = build_ai(cfg, api_key=key)
            result = ai.generate_commit_message([{"file": "ping.txt", "diff": "+ok"}])
            if result:
                return JSONResponse({"ok": True, "message": "Key works, sample generated."})
            return JSONResponse({"ok": False, "message": "Key reached the API but returned no text."})
        except Exception as exc:
            return JSONResponse({"ok": False, "message": f"Key test failed: {exc}"})

    # ----- history / stats -------------------------------------------------
    @app.get("/api/history")
    def history(limit: int = 50) -> JSONResponse:
        records: List[Dict[str, Any]] = build_history(cfg).load(limit=limit)
        return JSONResponse({"records": records})

    @app.get("/api/stats")
    def stats() -> JSONResponse:
        return JSONResponse(build_history(cfg).stats())

    @app.delete("/api/history")
    def clear_history() -> JSONResponse:
        build_history(cfg).clear()
        return JSONResponse({"ok": True})

    @app.get("/api/health")
    def health() -> JSONResponse:
        return JSONResponse({"ok": True})

    return app


def serve(open_browser: bool = True) -> None:
    """Boot the settings server and optionally open the browser."""
    import uvicorn

    cfg = ConfigManager()
    host = cfg.get("ui.host", "127.0.0.1")
    port = cfg.get("ui.port", 8420)
    url = f"http://{host}:{port}"

    app = create_app(cfg)

    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    print(f"Lazzy Commit settings: {url}")
    print("Press Ctrl+C to stop.")
    uvicorn.run(app, host=host, port=port, log_level="warning")
