import os
import sys
import io

# Fix Windows console encoding — prevents 'charmap' codec errors from Unicode in emails
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add 'service' to Python path so listener imports work
sys.path.append(os.path.join(os.path.dirname(__file__), 'service'))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import route modules
from routes.credentials import router as credentials_router
from routes.listener import router as listener_router
from routes.logs import router as logs_router

# ── App Setup ────────────────────────────────────────────
app = FastAPI(title="Phishing Attack Detector API")

# ── Register Routes ──────────────────────────────────────
app.include_router(credentials_router)
app.include_router(listener_router)
app.include_router(logs_router)

# ── Serve Frontend ───────────────────────────────────────
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))


# ── Run ──────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("[SERVER] Starting Phishing Detection Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
