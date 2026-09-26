"""Tool schemas + dispatcher for E.V.

Each entry in TOOLS is sent to the Voice Agent API in `session.update` so
the LLM knows what it can call. `dispatch_tool` executes the call and
returns either:
  - a plain string/dict result that gets spoken back (results should read
    naturally out loud -- this isn't an API response, it's spoken language), or
  - for `set_voice` / `end_session`, a dict with an `__action__` key that
    agent.py handles specially (it has to touch the WebSocket connection
    itself, which dispatch_tool has no access to).
"""

import json

import storage
import vision

VOICE_IDS = [
    "ivy", "alba", "eve", "george", "jane", "jean", "mary", "michael",
    "anna", "charles", "paul", "vera",
]

TOOLS = [
    {
        "type": "function",
        "name": "add_task",
        "description": (
            "Capture a new task or to-do item for Shiv. Use this whenever he says "
            "he needs to do something, has to finish something, or wants to remember "
            "to do something."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The task, in a short imperative phrase.",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "How urgent this is. Default to medium if unsure.",
                },
                "project": {
                    "type": "string",
                    "description": (
                        "Which project or hackathon this belongs to, if mentioned "
                        "(e.g. 'SWAP', 'LoRa test', 'coursework'). Omit if not said."
                    ),
                },
                "due_date": {
                    "type": "string",
                    "description": (
                        "Due date as YYYY-MM-DD, only if Shiv mentions a deadline "
                        "(e.g. 'tomorrow', 'by Friday', 'the 25th'). Work out the "
                        "actual calendar date yourself from today's date. Omit "
                        "entirely if no deadline was mentioned."
                    ),
                },
            },
            "required": ["title"],
        },
    },
    {
        "type": "function",
        "name": "list_tasks",
        "description": "List Shiv's tasks so you can read them back to him.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "completed", "all"],
                    "description": "Which tasks to list. Default to pending.",
                },
            },
        },
    },
    {
        "type": "function",
        "name": "complete_task",
        "description": (
            "Mark a task as done. Match it by whatever short description Shiv gives "
            "you -- it doesn't need to be exact."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "A phrase identifying which pending task is done.",
                },
            },
            "required": ["title"],
        },
    },
    {
        "type": "function",
        "name": "delete_task",
        "description": (
            "Permanently remove a task Shiv no longer wants tracked at all -- "
            "different from complete_task, which marks it done but keeps it "
            "around. Match by whatever description he gives, it doesn't need "
            "to be exact."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "A phrase identifying which task to delete.",
                },
            },
            "required": ["title"],
        },
    },
    {
        "type": "function",
        "name": "add_note",
        "description": (
            "Log a note, idea, or reminder that isn't an action item -- something "
            "Shiv wants recorded so he doesn't lose track of it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The note content."},
                "tag": {
                    "type": "string",
                    "description": "Optional short category, e.g. 'idea', 'EDC', 'SWAP'.",
                },
            },
            "required": ["text"],
        },
    },
    {
        "type": "function",
        "name": "delete_note",
        "description": (
            "Permanently remove a note. Match by whatever content Shiv gives, "
            "it doesn't need to be exact."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "A phrase identifying which note to delete.",
                },
            },
            "required": ["text"],
        },
    },
    {
        "type": "function",
        "name": "undo_last",
        "description": (
            "Undo the most recently added task or note from this conversation. "
            "Use this when Shiv says 'undo that', 'oops', 'scratch that', or "
            "'delete the last one' right after adding something -- no need to "
            "ask him to repeat what it was."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "search",
        "description": (
            "Search Shiv's tasks and notes by keyword. Use this when he asks "
            "whether he noted or logged something about a specific topic, e.g. "
            "'did I note anything about the sensor drift' or 'do I have a "
            "task about the LoRa module'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The keyword or phrase to search for.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "get_briefing",
        "description": (
            "Get a snapshot of pending task count, top priority tasks, anything "
            "overdue or due today, and recent notes so you can summarize it for "
            "Shiv in your own words."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "list_projects",
        "description": (
            "Group Shiv's tasks by which project they belong to, so you can give "
            "him a project-by-project rundown instead of one flat list. Use this "
            "when he asks what's going on across his projects, or names multiple "
            "projects at once."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "completed", "all"],
                    "description": "Which tasks to include. Default to pending.",
                },
            },
        },
    },
    {
        "type": "function",
        "name": "set_voice",
        "description": (
            "Switch the voice you speak with. Use this when Shiv asks to hear a "
            "different voice, a deeper voice, a different accent, and so on. This "
            "briefly restarts the voice session, so say something short like "
            "'switching voices' before you call it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "voice": {
                    "type": "string",
                    "enum": VOICE_IDS,
                    "description": "The voice ID to switch to.",
                },
            },
            "required": ["voice"],
        },
    },
    {
        "type": "function",
        "name": "remember_fact",
        "description": (
            "Save a durable fact about Shiv that should persist into future "
            "sessions -- his hardware, a preference, ongoing context. Not a "
            "task (use add_task) and not a one-off note (use add_note) -- "
            "this is specifically for things you should just *know* about "
            "him going forward."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "fact": {
                    "type": "string",
                    "description": "The fact, as a short, self-contained sentence.",
                },
            },
            "required": ["fact"],
        },
    },
    {
        "type": "function",
        "name": "read_screen",
        "description": (
            "Take a screenshot of Shiv's screen right now and answer a "
            "question about what's showing -- an error message, what's in a "
            "window, a general description. Use this whenever he asks about "
            "something visual on his display."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": (
                        "What to look for or answer about the screen. Default "
                        "to a general description if he didn't ask something "
                        "specific."
                    ),
                },
            },
        },
    },
    {
        "type": "function",
        "name": "end_session",
        "description": (
            "End the conversation cleanly. Call this when Shiv says goodbye, "
            "that he's done for now, or a similar closing phrase."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
]


def dispatch_tool(name: str, args):
    if isinstance(args, str):
        args = json.loads(args) if args else {}
    args = args or {}

    if name == "add_task":
        task = storage.add_task(
            title=args["title"],
            priority=args.get("priority", "medium"),
            project=args.get("project"),
            due_date=args.get("due_date"),
        )
        due = f", due {task['due_date']}" if task.get("due_date") else ""
        return f"Added: {task['title']} ({task['priority']} priority{due})."

    if name == "list_tasks":
        status = args.get("status", "pending")
        tasks = storage.list_tasks(status)
        if not tasks:
            return f"No {status} tasks." if status != "all" else "No tasks yet."
        titles = "; ".join(t["title"] for t in tasks)
        return f"{len(tasks)} {status} task(s): {titles}"

    if name == "complete_task":
        task = storage.complete_task(args["title"])
        if task is None:
            return f"I couldn't find a pending task matching '{args['title']}'."
        return f"Marked done: {task['title']}."

    if name == "delete_task":
        task = storage.delete_task(args["title"])
        if task is None:
            return f"I couldn't find a task matching '{args['title']}' to delete."
        return f"Deleted: {task['title']}."

    if name == "add_note":
        note = storage.add_note(text=args["text"], tag=args.get("tag"))
        return f"Noted: {note['text']}"

    if name == "delete_note":
        note = storage.delete_note(args["text"])
        if note is None:
            return f"I couldn't find a note matching '{args['text']}' to delete."
        return "Deleted that note."

    if name == "undo_last":
        item = storage.undo_last()
        if item is None:
            return "There's nothing to undo."
        if item["kind"] == "task":
            return f"Undone -- removed the task '{item['title']}'."
        return "Undone -- removed that note."

    if name == "search":
        result = storage.search(args["query"])
        if not result["tasks"] and not result["notes"]:
            return f"Nothing found matching '{args['query']}'."
        return json.dumps(result)

    if name == "get_briefing":
        b = storage.get_briefing()
        payload = {
            "pending_task_count": b["pending_count"],
            "top_tasks": b["top_tasks"],
            "overdue": b.get("overdue", []),
            "due_today": b.get("due_today", []),
            "recent_notes": b["recent_notes"],
        }
        return json.dumps(payload)

    if name == "list_projects":
        status = args.get("status", "pending")
        grouped = storage.list_by_project(status)
        if not grouped:
            return "No tasks yet."
        return json.dumps(grouped)

    if name == "remember_fact":
        entry = storage.remember(args["fact"])
        return f"I'll remember that: {entry['text']}"

    if name == "read_screen":
        question = args.get("question") or "What's on my screen right now?"
        return vision.read_screen(question)

    if name == "set_voice":
        voice = args.get("voice", "ivy")
        if voice not in VOICE_IDS:
            voice = "ivy"
        return {
            "__action__": "switch_voice",
            "voice": voice,
            "message": f"Switching to the {voice} voice now.",
        }

    if name == "end_session":
        return {
            "__action__": "end_session",
            "message": "Got it -- talk soon.",
        }

    return f"Unknown tool: {name}"
