"""Optional one-way sync: new tasks captured by voice -> a Notion database.

Meant to plug into an existing "Hackathon Command Center"-style Notion
workspace. Entirely optional — if NOTION_API_KEY or NOTION_TASKS_DB_ID
aren't set, every call here is a no-op. This keeps the live demo safe: it
never depends on Notion being configured correctly.

Setup (only if you want this on):
1. Create an integration at https://www.notion.so/my-integrations, copy
   its "Internal Integration Secret" into NOTION_API_KEY in .env.
2. Share your target Notion database with that integration
   (••• menu on the database -> Connections -> your integration).
3. Copy the database ID out of its URL into NOTION_TASKS_DB_ID in .env.
4. The database needs at minimum a title property (any name is fine —
   Notion always calls the title column "title" internally) and,
   optionally, a "Priority" select property; both are filled if present.
"""

import os
from typing import Optional

import requests

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_TASKS_DB_ID = os.environ.get("NOTION_TASKS_DB_ID")
NOTION_VERSION = "2022-06-28"
NOTION_PAGES_URL = "https://api.notion.com/v1/pages"


def _enabled() -> bool:
    return bool(NOTION_API_KEY and NOTION_TASKS_DB_ID)


def sync_task_to_notion(task: dict) -> Optional[dict]:
    if not _enabled():
        return None

    properties = {
        "Name": {"title": [{"text": {"content": task["title"]}}]},
    }
    if task.get("priority"):
        properties["Priority"] = {"select": {"name": task["priority"].capitalize()}}
    if task.get("project"):
        properties["Project"] = {"rich_text": [{"text": {"content": task["project"]}}]}

    resp = requests.post(
        NOTION_PAGES_URL,
        headers={
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
        json={
            "parent": {"database_id": NOTION_TASKS_DB_ID},
            "properties": properties,
        },
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()
