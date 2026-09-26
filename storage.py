"""Local JSON-backed storage for tasks and notes.

Kept deliberately simple (no DB) so the demo works offline and with zero
setup beyond this repo — a JSON file next to the code. If Notion
credentials are present (see notion_sync.py), new tasks are also mirrored
there, best-effort.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent / "data"
TASKS_FILE = DATA_DIR / "tasks.json"
NOTES_FILE = DATA_DIR / "notes.json"
MEMORY_FILE = DATA_DIR / "memory.json"

VALID_PRIORITIES = {"low", "medium", "high"}

# Tracks the single most recently created task or note *in this process*, so
# "undo that" works without Shiv having to repeat what he just said. Resets
# on a fresh `python agent.py` run -- that's intentional, undo only makes
# sense within the conversation that created the thing.
_last_created: Optional[dict] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(path: Path) -> list:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(path: Path, items: list) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    tmp.replace(path)


# ---------------------------------------------------------------- tasks ---

def add_task(
    title: str,
    priority: str = "medium",
    project: Optional[str] = None,
    due_date: Optional[str] = None,
) -> dict:
    priority = priority.lower() if priority else "medium"
    if priority not in VALID_PRIORITIES:
        priority = "medium"

    task = {
        "id": uuid.uuid4().hex[:8],
        "title": title.strip(),
        "priority": priority,
        "project": project,
        "due_date": due_date,  # YYYY-MM-DD, resolved by the LLM from relative speech
        "status": "pending",
        "created_at": _now(),
        "completed_at": None,
    }
    tasks = _load(TASKS_FILE)
    tasks.append(task)
    _save(TASKS_FILE, tasks)

    global _last_created
    _last_created = {"kind": "task", "id": task["id"]}

    # Best-effort mirror to Notion; never let this break the voice loop.
    try:
        from notion_sync import sync_task_to_notion

        sync_task_to_notion(task)
    except Exception as exc:  # noqa: BLE001 - demo must never crash on this
        print(f"[notion_sync] skipped: {exc}")

    return task


def list_tasks(status: str = "pending") -> list:
    tasks = _load(TASKS_FILE)
    if status == "all":
        return tasks
    return [t for t in tasks if t["status"] == status]


def complete_task(title: str) -> Optional[dict]:
    """Fuzzy-match a pending task by substring (case-insensitive) and mark it done.

    Returns the completed task dict, or None if nothing matched.
    """
    tasks = _load(TASKS_FILE)
    needle = title.strip().lower()

    match = None
    for t in tasks:
        if t["status"] == "pending" and needle in t["title"].lower():
            match = t
            break

    if match is None:
        return None

    match["status"] = "completed"
    match["completed_at"] = _now()
    _save(TASKS_FILE, tasks)
    return match


def delete_task(title: str) -> Optional[dict]:
    """Fuzzy-match a task by substring (any status) and remove it entirely.

    Different from complete_task -- this is for "actually, forget that
    task", not "I finished it"."""
    tasks = _load(TASKS_FILE)
    needle = title.strip().lower()

    match = next((t for t in tasks if needle in t["title"].lower()), None)
    if match is None:
        return None

    tasks = [t for t in tasks if t["id"] != match["id"]]
    _save(TASKS_FILE, tasks)
    return match


# ---------------------------------------------------------------- notes ---

def add_note(text: str, tag: Optional[str] = None) -> dict:
    note = {
        "id": uuid.uuid4().hex[:8],
        "text": text.strip(),
        "tag": tag,
        "created_at": _now(),
    }
    notes = _load(NOTES_FILE)
    notes.append(note)
    _save(NOTES_FILE, notes)

    global _last_created
    _last_created = {"kind": "note", "id": note["id"]}

    return note


def list_notes(limit: int = 5) -> list:
    notes = _load(NOTES_FILE)
    return notes[-limit:][::-1]


def delete_note(text: str) -> Optional[dict]:
    """Fuzzy-match a note by substring and remove it entirely."""
    notes = _load(NOTES_FILE)
    needle = text.strip().lower()

    match = next((n for n in notes if needle in n["text"].lower()), None)
    if match is None:
        return None

    notes = [n for n in notes if n["id"] != match["id"]]
    _save(NOTES_FILE, notes)
    return match


def undo_last() -> Optional[dict]:
    """Remove whichever task or note was most recently added in this run.

    Returns the removed item (with a 'kind' key: 'task' or 'note'), or None
    if there's nothing tracked to undo."""
    global _last_created
    if _last_created is None:
        return None

    kind, item_id = _last_created["kind"], _last_created["id"]
    _last_created = None

    if kind == "task":
        tasks = _load(TASKS_FILE)
        match = next((t for t in tasks if t["id"] == item_id), None)
        if match is None:
            return None
        _save(TASKS_FILE, [t for t in tasks if t["id"] != item_id])
        return {"kind": "task", **match}

    notes = _load(NOTES_FILE)
    match = next((n for n in notes if n["id"] == item_id), None)
    if match is None:
        return None
    _save(NOTES_FILE, [n for n in notes if n["id"] != item_id])
    return {"kind": "note", **match}


# --------------------------------------------------------------- search ---

def search(query: str) -> dict:
    """Keyword search across task titles/projects and note text/tags."""
    needle = query.strip().lower()

    tasks = _load(TASKS_FILE)
    matching_tasks = [
        t["title"]
        for t in tasks
        if needle in t["title"].lower() or needle in (t.get("project") or "").lower()
    ]

    notes = _load(NOTES_FILE)
    matching_notes = [
        n["text"]
        for n in notes
        if needle in n["text"].lower() or needle in (n.get("tag") or "").lower()
    ]

    return {"tasks": matching_tasks, "notes": matching_notes}


# --------------------------------------------------------- by project ---

def list_by_project(status: str = "pending") -> dict:
    """Group tasks by their `project` field. Tasks with no project land
    under 'Unsorted'."""
    tasks = list_tasks(status)
    grouped: dict = {}
    for t in tasks:
        key = t.get("project") or "Unsorted"
        grouped.setdefault(key, []).append(t["title"])
    return grouped


# -------------------------------------------------------------- memory ---

def remember(fact: str) -> dict:
    """Save a durable fact about Shiv that should persist across sessions
    (and across voice-switch reconnects, since it's read fresh into the
    system prompt each time)."""
    entry = {
        "id": uuid.uuid4().hex[:8],
        "text": fact.strip(),
        "created_at": _now(),
    }
    memories = _load(MEMORY_FILE)
    memories.append(entry)
    _save(MEMORY_FILE, memories)
    return entry


def get_memories(limit: int = 20) -> list:
    """Most recent remembered facts, oldest of the recent batch first (so
    they read naturally in a system prompt)."""
    memories = _load(MEMORY_FILE)
    return [m["text"] for m in memories[-limit:]]


# ------------------------------------------------------------- briefing ---

def get_briefing() -> dict:
    pending = list_tasks("pending")
    today = datetime.now(timezone.utc).date().isoformat()

    overdue = [t["title"] for t in pending if t.get("due_date") and t["due_date"] < today]
    due_today = [t["title"] for t in pending if t.get("due_date") == today]

    pending_sorted = sorted(
        pending,
        key=lambda t: {"high": 0, "medium": 1, "low": 2}.get(t["priority"], 1),
    )
    return {
        "pending_count": len(pending),
        "top_tasks": [t["title"] for t in pending_sorted[:3]],
        "overdue": overdue,
        "due_today": due_today,
        "recent_notes": [n["text"] for n in list_notes(3)],
    }
