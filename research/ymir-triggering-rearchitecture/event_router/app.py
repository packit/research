"""
Ymir Event Router (POC) - receives POST requests from Jira Automation
manual trigger forms and routes to Redis queues for agent processing.
"""

import json
import logging
import os
from datetime import datetime, timezone

import redis
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://valkey:6379/0")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

# Queue names — mirroring common/constants.py from ai-workflows
TRIAGE_QUEUE = "triage_queue"
BACKPORT_QUEUE_C9S = "backport_queue_c9s"
BACKPORT_QUEUE_C10S = "backport_queue_c10s"
REBASE_QUEUE_C9S = "rebase_queue_c9s"
REBASE_QUEUE_C10S = "rebase_queue_c10s"


def _use_c9s_branch(branch: str) -> bool:
    branch_lower = branch.lower()
    return any(p in branch_lower for p in ("rhel-9", "c9s", "rhel-8", "c8s"))


def get_queue_for_action(action: str, branch: str | None) -> str:
    if action == "triage":
        return TRIAGE_QUEUE
    elif action == "backport":
        if branch and _use_c9s_branch(branch):
            return BACKPORT_QUEUE_C9S
        return BACKPORT_QUEUE_C10S
    elif action == "rebase":
        if branch and _use_c9s_branch(branch):
            return REBASE_QUEUE_C9S
        return REBASE_QUEUE_C10S
    raise ValueError(f"Unknown action: {action}")


def empty_to_none(value: str | None) -> str | None:
    """Jira Automation sends empty strings for unfilled optional fields."""
    return value if value else None


class EventResponse(BaseModel):
    status: str
    action: str
    issue: str
    queue: str


app = FastAPI(title="Ymir Event Router (POC)")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/webhook", response_model=EventResponse)
async def handle_event(request: Request):
    """
    Receive POST from Jira Automation manual trigger forms.

    Expected payload (configured in Jira Automation "Send web request" action
    with "Custom data" body):
    {
        "issue_key": "{{issue.key}}",
        "action": "backport",
        "upstream_fix": "{{userInputs.upstream_fix}}",
        "branch": "{{userInputs.branch}}",
        "version": "{{userInputs.version}}",
        "instructions": "{{userInputs.instructions}}",
        "author_id": "{{initiator.accountId}}"
    }

    Note: "action" is hardcoded per rule (one rule per workflow).
    "author_id" uses {{initiator}}, not {{userInputs}} — it's the
    person who clicked the trigger, not a form field.
    """
    # Validate shared secret if configured
    if WEBHOOK_SECRET:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {WEBHOOK_SECRET}":
            raise HTTPException(status_code=401, detail="Unauthorized")

    payload = await request.json()
    logger.info("Received event: %s", json.dumps(payload, indent=2))

    issue_key = payload.get("issue_key")
    if not issue_key:
        raise HTTPException(status_code=400, detail="Missing issue_key")

    action = payload.get("action")
    if not action or action not in ("triage", "backport", "rebase"):
        raise HTTPException(status_code=400, detail="Invalid or missing action")

    branch = empty_to_none(payload.get("branch"))
    upstream_fix = empty_to_none(payload.get("upstream_fix"))
    version = empty_to_none(payload.get("version"))
    instructions = empty_to_none(payload.get("instructions"))
    author_id = empty_to_none(payload.get("author_id"))
    triggered_at = datetime.now(timezone.utc).isoformat()

    # Validate required fields per action
    if action == "backport" and not upstream_fix:
        raise HTTPException(status_code=400, detail="Backport requires upstream_fix")
    if action == "rebase" and not version:
        raise HTTPException(status_code=400, detail="Rebase requires version")
    if action in ("backport", "rebase") and not branch:
        raise HTTPException(status_code=400, detail=f"{action} requires branch")

    # Route to queue
    queue = get_queue_for_action(action, branch)

    # Build queue payload matching the Task model format from ai-workflows
    if action == "triage":
        # Match existing Task.from_issue() format
        queue_payload = {
            "metadata": {"issue": issue_key},
            "attempts": 0,
        }
    else:
        queue_payload = {
            "metadata": {
                "jira_issue": issue_key,
                "action": action,
                "upstream_fix": upstream_fix,
                "version": version,
                "branch": branch,
                "instructions": instructions,
                "triggered_by": author_id,
                "triggered_at": triggered_at,
            },
            "attempts": 0,
        }

    r = redis.Redis.from_url(REDIS_URL)
    try:
        r.rpush(queue, json.dumps(queue_payload))
    finally:
        r.close()

    logger.info("Queued %s for %s -> %s", action, issue_key, queue)

    return EventResponse(status="queued", action=action, issue=issue_key, queue=queue)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
