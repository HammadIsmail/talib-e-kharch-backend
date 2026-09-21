import os
import sys
import traceback

# Ensure the root project directory is on sys.path so 'app' is importable on Vercel
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from app.main import app
except Exception as e:
    err_msg = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse

    app = FastAPI(title="Error")

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    async def debug_error(full_path: str):
        return PlainTextResponse(f"Talib-e-Kharch Backend Startup Error:\n\n{err_msg}", status_code=500)
