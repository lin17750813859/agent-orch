import hashlib
import hmac
import json
import logging
import os
import subprocess
import sys
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook-receiver")

app = FastAPI(title="Webhook Receiver")

GITHUB_SECRET = os.getenv("GITHUB_SECRET", "change-me")
GITLAB_SECRET = os.getenv("GITLAB_SECRET", "change-me")
AGENT_SCRIPT = os.getenv("AGENT_SCRIPT", "agent_task.py")


class WebhookPayload(BaseModel):
    repository: Optional[dict] = None
    ref: Optional[str] = None
    action: Optional[str] = None


def verify_github_signature(payload_body: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    expected = hmac.new(
        GITHUB_SECRET.encode(), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)


def verify_gitlab_token(token: str) -> bool:
    return hmac.compare_digest(token, GITLAB_SECRET)


def trigger_agent_task(event_type: str, payload: dict):
    try:
        result = subprocess.run(
            [sys.executable, AGENT_SCRIPT],
            input=json.dumps({"event": event_type, "payload": payload}),
            capture_output=True,
            text=True,
            timeout=30,
        )
        logger.info(f"Agent task completed: {result.stdout}")
        if result.stderr:
            logger.error(f"Agent task error: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("Agent task timed out")
    except Exception as e:
        logger.error(f"Agent task failed: {e}")


@app.post("/webhook")
async def webhook_receiver(request: Request):
    body = await request.body()
    headers = request.headers

    event_type = headers.get("X-GitHub-Event") or headers.get("X-Gitlab-Event")
    if not event_type:
        raise HTTPException(status_code=400, detail="Missing event header")

    if heade