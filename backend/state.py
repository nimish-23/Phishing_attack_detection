"""
Shared application state used by both server.py and route handlers.
Holds credentials, listener thread, logs, and helper functions.
"""

import threading
from datetime import datetime

# ── Shared State ─────────────────────────────────────────
state = {
    "status": "idle",        # idle | connecting | listening | error | stopped
    "email": None,
    "password": None,
    "error": None,
    "thread": None,
    "stop_event": None,
    "logs": [],              # list of {time, level, message}
}

MAX_LOGS = 200


# ── Log Capture ──────────────────────────────────────────
def log_callback(level: str, message: str):
    """Called by the listener thread to push logs into shared state."""
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message,
    }
    state["logs"].append(entry)

    # Keep bounded
    if len(state["logs"]) > MAX_LOGS:
        state["logs"] = state["logs"][-MAX_LOGS:]

    # Auto-detect status from log messages
    if "[LISTENING]" in message:
        state["status"] = "listening"
    elif "[ERROR]" in message and "Connection failed" in message:
        state["status"] = "error"
        state["error"] = message


# ── Listener Thread Wrapper ──────────────────────────────
def run_listener(email: str, password: str, stop_event: threading.Event):
    """Runs the IMAP listener in a background thread."""
    from service.listener import start_idle_listener

    try:
        state["status"] = "connecting"
        start_idle_listener(
            user_email=email,
            password=password,
            stop_event=stop_event,
            log_callback=log_callback,
        )
    except Exception as e:
        state["status"] = "error"
        state["error"] = str(e)
        log_callback("error", f"[ERROR] Thread crashed: {e}")
    finally:
        if state["status"] not in ("error",):
            state["status"] = "stopped"
        state["thread"] = None
