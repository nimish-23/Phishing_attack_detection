"""
API route: /api/credentials
Handles saving Gmail credentials for the IMAP listener.
"""

import threading
from fastapi import APIRouter
from pydantic import BaseModel
from state import state, log_callback

router = APIRouter()


class CredentialsPayload(BaseModel):
    email: str
    password: str


@router.post("/api/credentials")
def set_credentials(payload: CredentialsPayload):
    """Save credentials for later use by the listener."""
    # If listener is running, stop it first
    if state["thread"] and state["thread"].is_alive():
        state["stop_event"].set()
        state["thread"].join(timeout=10)

    state["email"] = payload.email
    state["password"] = payload.password
    state["status"] = "idle"
    state["error"] = None
    log_callback("success", f"Credentials set for {payload.email}")
    log_callback("info", "GMAIL_PASS_KEY loaded — IMAP connection ready")
    return {"ok": True, "message": "Credentials saved"}
