"""Screen reading: take a screenshot and ask Claude's vision API about it.

Entirely optional, same pattern as notion_sync.py -- if ANTHROPIC_API_KEY
isn't set, `read_screen` degrades to a friendly spoken message instead of
crashing the voice loop. This calls a separate vision-capable model purely
to *describe* the screenshot in text; AssemblyAI's own Voice Agent LLM is
still the one deciding when to call this tool and phrasing what gets said
out loud -- this doesn't replace anything AssemblyAI's API does.

Setup (only if you want this on):
1. Get an API key at https://console.anthropic.com/.
2. Put it in ANTHROPIC_API_KEY in .env.
"""

import base64
import io
import os

import requests

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_VISION_MODEL", "claude-haiku-4-5-20251001")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


def is_configured() -> bool:
    return bool(ANTHROPIC_API_KEY)


def _capture_screenshot_png() -> bytes:
    # Imported lazily so a missing Pillow install only breaks this one
    # feature, not the whole agent.
    from PIL import ImageGrab

    image = ImageGrab.grab()
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def read_screen(question: str = "What's on my screen right now?") -> str:
    if not is_configured():
        return (
            "Screen reading isn't set up -- add an ANTHROPIC_API_KEY to your "
            ".env file to turn it on."
        )

    try:
        png_bytes = _capture_screenshot_png()
    except Exception as exc:  # noqa: BLE001 -- never crash the voice loop
        return f"I couldn't take a screenshot: {exc}"

    image_b64 = base64.b64encode(png_bytes).decode()

    try:
        response = requests.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": (
                                    f"{question}\n\nAnswer in 1-3 short spoken "
                                    "sentences -- this gets read aloud by a "
                                    "voice assistant, so no markdown, no lists."
                                ),
                            },
                        ],
                    }
                ],
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        parts = [
            block["text"]
            for block in data.get("content", [])
            if block.get("type") == "text"
        ]
        return " ".join(parts).strip() or "I looked, but couldn't make anything out."
    except requests.exceptions.RequestException as exc:
        return f"I couldn't read the screen: {exc}"
