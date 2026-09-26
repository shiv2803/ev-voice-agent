import asyncio
import base64
import json
import os
import sys

import websockets
from dotenv import load_dotenv

import storage
from audio import Mic, Speaker
from prompts import build_greeting, build_system_prompt
from tools import TOOLS, dispatch_tool

load_dotenv()

ASSEMBLYAI_API_KEY = os.environ["ASSEMBLYAI_API_KEY"]
VOICE_AGENT_WS_URL = "wss://agents.assemblyai.com/v1/ws"
DEFAULT_VOICE = os.environ.get("EV_VOICE", "ivy")


class SwitchVoice(Exception):
    """Raised to tear down the current session and reconnect with a new
    voice -- output.voice is immutable for the lifetime of a WebSocket
    connection, so 'switching voices' means a fresh session.update on a
    fresh connection, not a live change mid-call."""

    def __init__(self, voice: str):
        self.voice = voice


class EndSession(Exception):
    """Raised when the user says goodbye -- session.end has already been
    sent by the time this is raised."""


async def run_session(voice: str, greeting: str) -> None:
    mic = Mic()
    speaker = Speaker()

    session_config = {
        "type": "session.update",
        "session": {
            "system_prompt": build_system_prompt(storage.get_memories()),
            "greeting": greeting,
            "tools": TOOLS,
            "output": {"voice": voice},
        },
    }

    async with websockets.connect(
        VOICE_AGENT_WS_URL,
        additional_headers={"Authorization": f"Bearer {ASSEMBLYAI_API_KEY}"},
    ) as ws:
        await ws.send(json.dumps(session_config))

        ready = asyncio.Event()
        pending_tools: list[dict] = []
        pending_action: dict | None = None
        loop = asyncio.get_event_loop()

        async def send_audio():
            await ready.wait()
            mic.start()
            while True:
                chunk = await loop.run_in_executor(None, mic.queue.get)
                await ws.send(json.dumps({
                    "type": "input.audio",
                    "audio": base64.b64encode(chunk).decode(),
                }))

        async def receive_events():
            nonlocal pending_action
            async for raw in ws:
                event = json.loads(raw)
                kind = event.get("type")

                if kind == "session.ready":
                    ready.set()
                    print(f"Session ready: {event.get('session_id')}")

                elif kind == "reply.audio":
                    speaker.play(base64.b64decode(event["data"]))

                elif kind == "tool.call":
                    result = dispatch_tool(event["name"], event.get("arguments", {}))
                    if isinstance(result, dict) and "__action__" in result:
                        # set_voice / end_session -- the actual side effect
                        # happens below, after the tool.result round-trip
                        # completes, since it touches the connection itself.
                        pending_action = result
                        value = result["message"]
                    else:
                        value = result
                    pending_tools.append({
                        "call_id": event["call_id"],
                        "result": value,
                    })

                elif kind == "reply.done":
                    if event.get("status") == "interrupted":
                        pending_tools.clear()
                        pending_action = None
                        speaker.flush_and_restart()
                    elif pending_tools:
                        for tool in pending_tools:
                            value = tool["result"]
                            if not isinstance(value, str):
                                value = json.dumps(value)
                            await ws.send(json.dumps({
                                "type": "tool.result",
                                "call_id": tool["call_id"],
                                "result": value,
                            }))
                        pending_tools.clear()

                        if pending_action:
                            action = pending_action
                            pending_action = None
                            await ws.send(json.dumps({"type": "session.end"}))
                            if action["__action__"] == "end_session":
                                raise EndSession()
                            elif action["__action__"] == "switch_voice":
                                raise SwitchVoice(action["voice"])

                elif kind == "transcript.user":
                    print(f"You:   {event['text']}")

                elif kind == "transcript.agent":
                    print(f"E.V.:  {event['text']}")

                elif kind == "session.error":
                    print(f"Session error [{event.get('code')}]: {event.get('message')}")

        try:
            await asyncio.gather(send_audio(), receive_events())
        finally:
            mic.stop()
            speaker.close()


def main():
    print("E.V. is listening. Start speaking. Ctrl+C to exit.\n")
    voice = DEFAULT_VOICE
    # Proactive greeting: mentions overdue/due-today tasks immediately on
    # connect, before Shiv even asks. Only for the *first* connection --
    # a voice-switch reconnect overrides this with its own "switched"
    # greeting further down.
    greeting = build_greeting(storage.get_briefing())
    try:
        while True:
            try:
                asyncio.run(run_session(voice, greeting))
                break  # server closed the connection on its own -- exit
            except EndSession:
                print("\nSession ended.")
                break
            except SwitchVoice as switch:
                voice = switch.voice
                greeting = f"Switched -- this is the {voice} voice now."
                print(f"\n[reconnecting with voice '{voice}'...]\n")
                continue
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nGoodbye.")
    sys.exit(0)


if __name__ == "__main__":
    main()
