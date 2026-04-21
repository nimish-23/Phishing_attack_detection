"""
API routes: /api/start, /api/stop, /api/status
Controls the IMAP IDLE listener lifecycle.
"""

import threading
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from state import state, log_callback, run_listener

router = APIRouter()


@router.post("/api/start")
def start_listener():
    """Start the IMAP IDLE listener in a background thread."""
    if not state["email"] or not state["password"]:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "message": "Set credentials first"},
        )

    if state["thread"] and state["thread"].is_alive():
        return JSONResponse(
            status_code=409,
            content={"ok": False, "message": "Listener is already running"},
        )

    stop_event = threading.Event()
    state["stop_event"] = stop_event
    state["error"] = None

    thread = threading.Thread(
        target=run_listener,
        args=(state["email"], state["password"], stop_event),
        daemon=True,
    )
    state["thread"] = thread
    thread.start()

    return {"ok": True, "message": "Listener started"}


@router.post("/api/stop")
def stop_listener():
    """Signal the listener thread to stop gracefully."""
    if not state["thread"] or not state["thread"].is_alive():
        state["status"] = "idle"
        return {"ok": True, "message": "Listener was not running"}

    state["stop_event"].set()
    state["thread"].join(timeout=10)
    state["status"] = "stopped"
    log_callback("warn", "IMAP connection closed")
    return {"ok": True, "message": "Listener stopped"}


@router.get("/api/status")
def get_status():
    """Return the current listener status."""
    return {
        "status": state["status"],
        "email": state["email"],
        "error": state["error"],
    }
