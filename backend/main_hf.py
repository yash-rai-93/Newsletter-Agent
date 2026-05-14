"""
main_hf.py  —  Hugging Face Spaces entry point
-----------------------------------------------
Extends the regular FastAPI app to also serve the pre-built
React frontend as static files.  All /api/* routes from
main.py are inherited unchanged.

  uvicorn backend.main_hf:app --host 0.0.0.0 --port 7860
"""

import os
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request

# Re-use every route registered in main.py
from .main import app

STATIC_DIR = Path(__file__).parent.parent / "static"


def _mount_static():
    """Mount /assets if the frontend has been built."""
    assets = STATIC_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")


_mount_static()


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(request: Request, full_path: str = ""):
    """
    Serve index.html for every path that isn't an API route,
    so that React Router works on direct URL loads.
    """
    # /api/* and /health are handled by routes already registered
    if full_path.startswith("api/") or full_path in ("health",):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Not Found"}, status_code=404)

    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
    # Dev fallback
    return FileResponse(str(Path(__file__).parent.parent / "frontend" / "index.html"))
