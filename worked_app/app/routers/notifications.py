from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from typing import Optional
import time
import pathlib

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ---------------------------
# Task functions
# ---------------------------

def write_file(path: str, content: str):
    """Simulates slow I/O (e.g., emailing, webhook call)."""
    # simulate delay
    time.sleep(1)
    p = pathlib.Path(path)
    p.write_text(content)


def send_email(email: str, subject: str, body: str):
    # Replace with real email client (e.g., SMTP/SendGrid)
    time.sleep(1)
    print(f"[EMAIL] to={email} subject={subject} body={body[:40]}...")


# ---------------------------
# Dependency that can enqueue a task
# ---------------------------

def queue_audit(background_tasks: BackgroundTasks, action: str | None = None):
    if action:
        background_tasks.add_task(write_file, "audit.log", f"action={action}\n")
    return action


# ---------------------------
# Routes using @router.api_route
# ---------------------------

@router.api_route("/send", methods=["POST"])
async def queue_email(
        email: str,
        subject: str = "Welcome!",
        body: str = "Thanks for signing up.",
        background_tasks: BackgroundTasks = None,
):
    if background_tasks is None:
        raise HTTPException(500, "BackgroundTasks missing")
    background_tasks.add_task(send_email, email, subject, body)
    return {"status": "queued", "to": email}


@router.api_route("/save-log", methods=["POST"])
async def save_log(
        message: str,
        file_path: str = "log.txt",
        background_tasks: BackgroundTasks = None,
):
    if background_tasks is None:
        raise HTTPException(500, "BackgroundTasks missing")
    background_tasks.add_task(write_file, file_path, message + "\n")
    return {"status": "queued", "file": file_path}


@router.api_route("/search", methods=["GET"])
async def search(
        q: Optional[str] = Depends(queue_audit),  # queues audit write if q provided
):
    # do your search quickly; audit writes after response
    return {"q": q, "results": []}
