"""
API route: /api/logs
Returns log entries for the frontend to poll.
"""

from fastapi import APIRouter
from state import state

router = APIRouter()


@router.get("/api/logs")
def get_logs(since: int = 0):
    """
    Return log entries starting from index `since`.
    The frontend polls this endpoint and passes the last known index.
    """
    entries = state["logs"][since:]
    return {
        "logs": entries,
        "total": len(state["logs"]),
    }
