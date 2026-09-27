<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:1a1a2e,100:16213e&height=220&section=header&text=E.V.&fontSize=90&fontColor=00d4ff&animation=twinkling&fontAlignY=38&desc=Your%20Hands-Free%20Voice%20Agent&descAlignY=58&descSize=22&descColor=ffffff" width="100%"/>

<br/>

[![Typing SVG](https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=20&duration=2800&pause=1000&color=00D4FF&center=true&vCenter=true&multiline=false&width=750&lines=Always+listening.+Never+in+the+way.;14+tools.+One+voice+command.;Barge+in+anytime+%E2%80%94+E.V.+yields+instantly.;Capture+tasks+%26+notes+hands-free.;Get+a+spoken+briefing+before+you+even+ask.;Built+for+the+AssemblyAI+Voice+Agent+Hackathon.)](https://git.io/typing-svg)

<br/>

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![AssemblyAI](https://img.shields.io/badge/AssemblyAI-Voice%20Agent%20API-FF6B35?style=for-the-badge&logo=microphone&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-Real--Time-4CAF50?style=for-the-badge&logo=socketdotio&logoColor=white)
![Claude Vision](https://img.shields.io/badge/Claude-Vision%20API-8B5CF6?style=for-the-badge&logo=anthropic&logoColor=white)
![Status](https://img.shields.io/badge/Status-Feature%20Complete-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

<br/>

[![lablab.ai submission](https://img.shields.io/badge/🏆%20lablab.ai-Barge--In%20Submission-blueviolet?style=for-the-badge)](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/barge-in/submission)

<br/>

> **E.V.** is a hands-free personal productivity voice agent — always listening, never in the way.  
> Capture tasks and notes while you're heads-down building. Get a spoken briefing on demand.  
> Powered by **AssemblyAI's Voice Agent API** over a single persistent WebSocket.

</div>

---

## 🎬 Demo

<div align="center">

> 📽️ *Demo video coming soon — recording in progress*

</div>

---

## ⚡ What Makes E.V. Different

<div align="center">

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│   Traditional approach          │   E.V.                                      │
│   ─────────────────────────     │   ────────────────────────────────────      │
│   Stop → Open app               │   Just talk                                 │
│   Type task → Save              │   "Add a task to fix the auth bug by Fri"   │
│   Switch tab → Check tasks      │   "Give me a briefing"                      │
│   Forget things between runs    │   "Remember that I prefer short answers"    │
│                                 │                                             │
└───────────────────────────────────────────────────────────────────────────────┘
```

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎙️ Voice-First, Always-On
- No wake word required — just start talking
- Barge-in supported: interrupt E.V. any time
- Single WebSocket connection handles STT → LLM → TTS in one round trip
- Natural conversational flow, not command syntax

</td>
<td width="50%">

### 🧠 Gets Smarter Over Time
- `remember_fact` persists facts to `data/memory.json`
- System prompt rebuilt fresh each session with everything E.V. knows about you
- Proactive greeting: overdue tasks called out *before* you ask
- Sessions feel personal — not generic

</td>
</tr>
<tr>
<td width="50%">

### 📋 Full Task & Note Management
- Add tasks with optional due dates
- Mark tasks complete, delete them, or undo the last one
- Add and delete notes by voice
- Keyword search across all tasks *and* notes

</td>
<td width="50%">

### 🎭 Optional Power Features
- **Screen Vision**: say "what's on my screen?" — E.V. takes a screenshot and describes it via Claude Vision
- **Notion Sync**: every new task mirrors to your Notion database
- **12 Voice Options**: switch voices live; E.V. reconnects cleanly
- All optional — E.V. degrades gracefully if keys are unset

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
                        ┌─────────────────────┐
                        │     You (speak)      │
                        └──────────┬──────────┘
                                   │
                         mic audio via sounddevice
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                     agent.py  ─  WebSocket Loop                  │
│                                                                  │
│  ┌───────────┐  ┌────────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ audio.py  │  │ prompts.py │  │ tools.py │  │ storage.py  │  │
│  │ mic/spkr  │  │ sys prompt │  │ 14 tools │  │ JSON on disk│  │
│  │ sounddev. │  │ + greeting │  │ dispatcher│  │ tasks/notes │  │
│  └───────────┘  └────────────┘  └──────────┘  │ /memory     │  │
│                                                └─────────────┘  │
│  ┌──────────────────────┐  ┌────────────────────────────────┐   │
│  │     vision.py        │  │       notion_sync.py           │   │
│  │ read_screen (opt.)   │  │  best-effort Notion mirror     │   │
│  │ screenshot + Claude  │  │  (opt., new tasks only)        │   │
│  └──────────────────────┘  └────────────────────────────────┘   │
└────────────────────────────┬─────────────────────────────────────┘
                             │ Single persistent WebSocket
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│               AssemblyAI Voice Agent API (cloud)                 │
│                                                                  │
│         🎙️ STT ──► 🧠 LLM Reasoning ──► 🔧 Tool Dispatch         │
│                         ◄──── 🔊 TTS ◄────                       │
└────────────────────────────┬─────────────────────────────────────┘
                             │ synthesized audio
                             ▼
                    ┌────────────────────┐
                    │   You (hear E.V.)  │
                    └────────────────────┘
```

---

## 🔧 14 Tools

<details>
<summary><b>📋 Task Management (5 tools)</b> — click to expand</summary>

<br/>

| Tool | Voice Example | Notes |
|---|---|---|
| `add_task` | *"Add a task to write the README by tomorrow"* | Optional `due_date` parameter |
| `list_tasks` | *"What's on my list?"* | Returns all pending tasks |
| `complete_task` | *"Mark the README task as done"* | Fuzzy name match |
| `delete_task` | *"Delete the README task"* | Permanent remove |
| `get_briefing` | *"Give me a briefing"* | Surfaces overdue + due-today tasks |

</details>

<details>
<summary><b>📝 Notes (2 tools)</b> — click to expand</summary>

<br/>

| Tool | Voice Example | Notes |
|---|---|---|
| `add_note` | *"Take a note: ping the team at 3pm"* | Free-form text |
| `delete_note` | *"Delete the 3pm note"* | By fuzzy name match |

</details>

<details>
<summary><b>🛠️ Utilities (7 tools)</b> — click to expand</summary>

<br/>

| Tool | Voice Example | Notes |
|---|---|---|
| `undo_last` | *"Undo that"* | Removes last task OR note added this session |
| `search` | *"Search for anything about the API"* | Searches tasks + notes together |
| `list_projects` | *"What projects do I have?"* | Lists project categories |
| `remember_fact` | *"Remember that I prefer concise answers"* | Persists to `memory.json`, injected every session |
| `set_voice` | *"Switch to a different voice"* | 12 voice IDs; triggers clean reconnect |
| `end_session` | *"Goodbye"* or *"End session"* | Clean WebSocket close |
| `read_screen` | *"What's on my screen?"* | Screenshot → Claude Vision → spoken description *(optional)* |

</details>

---

## 🚀 Quick Start

### 1. Prerequisites

- Python **3.10+**
- Windows / macOS / Linux with a working microphone
- An **[AssemblyAI API key](https://www.assemblyai.com/)** *(required)*
- An **[Anthropic API key](https://www.anthropic.com/)** *(optional — for `read_screen`)*
- A **[Notion integration token](https://developers.notion.com/)** *(optional — for Notion sync)*

---

### 2. Clone & Install

```bash
git clone https://github.com/shiv2803/ev-voice-agent
cd ev-voice-agent
pip install -r requirements.txt
```

> **Windows note:** `sounddevice` is used instead of PyAudio to avoid the common Windows build-chain issue. It installs cleanly via pip.

---

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env`:

```env
# ── Required ───────────────────────────────────────────────────────────────────
ASSEMBLYAI_API_KEY=your_assemblyai_key_here

# ── Optional: Screen Vision ────────────────────────────────────────────────────
ANTHROPIC_API_KEY=your_anthropic_key_here

# ── Optional: Notion Sync ──────────────────────────────────────────────────────
NOTION_API_KEY=your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id
```

---

### 4. Run

```bash
python agent.py
```

E.V. connects to AssemblyAI, checks for overdue tasks, and greets you.  
**Just start talking.**

---

## 🗣️ Example Voice Commands

```bash
# Tasks
"Add a task to review the PR by Friday"
"What's on my list?"
"Mark the PR review as done"
"Delete the PR review task"
"Undo that"

# Notes
"Take a note: the API rate limit is 100 requests per minute"
"Delete the rate limit note"

# Briefing & Search
"Give me a briefing"
"Search for anything about the API"

# Memory & Personality
"Remember that I prefer bullet points over paragraphs"
"Remember that my team's standup is at 10am"

# Screen & Voice
"What's on my screen right now?"
"Switch to a different voice"

# End
"That's all, goodbye"
```

---

## 📁 Project Structure

```
ev-voice-agent/
│
├── agent.py            ← Main entry point. WebSocket loop, event routing,
│                         barge-in, voice-switch reconnects, session end.
│
├── audio.py            ← Mic input + speaker output via sounddevice.
│
├── prompts.py          ← Builds system prompt each session (injects date
│                         + remembered facts). build_greeting() checks for
│                         overdue tasks proactively.
│
├── tools.py            ← 14 tool JSON schemas + dispatcher function.
│
├── storage.py          ← Local JSON persistence. Tracks _last_created
│                         for undo_last.
│
├── vision.py           ← Optional. Screenshot + Claude Vision API call.
│                         Registers read_screen only if ANTHROPIC_API_KEY set.
│
├── notion_sync.py      ← Optional. Best-effort Notion mirror on add_task.
│
├── requirements.txt    ← websockets, python-dotenv, sounddevice,
│                         requests, Pillow
│
├── .env.example        ← Copy to .env and fill in your keys.
│
└── data/               ← Auto-created at first run.
    ├── tasks.json
    ├── notes.json
    └── memory.json
```

---

## 🔍 How Barge-In Works

AssemblyAI's Voice Agent API natively supports barge-in — when E.V. is speaking, you can interrupt and it yields immediately. No manual implementation needed. This is a first-class feature of the API, not a workaround.

---

## 🎭 Voice Switching

`output.voice` is **immutable for the life of a WebSocket connection** per AssemblyAI's specification. E.V. handles this correctly: switching voices triggers a clean `session.end` followed by a new connection with the updated voice ID. The handoff is transparent — E.V. confirms the switch in the new voice.

---

## 🧪 Running Without Optional Keys

| What's missing | What happens |
|---|---|
| No `ANTHROPIC_API_KEY` | `read_screen` tool is simply not registered. Everything else works normally. |
| No `NOTION_API_KEY` / `NOTION_DATABASE_ID` | Notion sync is silently skipped. Tasks are still saved locally. |
| Both missing | E.V. runs on AssemblyAI alone — full 12-tool feature set, no vision, no Notion. |

---

## 🏆 Built For

<div align="center">

[![AssemblyAI Voice Agent Hackathon](https://img.shields.io/badge/AssemblyAI-Voice%20Agent%20Hackathon%202026-FF6B35?style=for-the-badge)](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon)

**Team:** Barge-In &nbsp;|&nbsp; **Solo build** &nbsp;|&nbsp; **Deadline:** September 30, 2026

</div>

---

## 📄 License

```
MIT License

Copyright (c) 2026 Shiv — Team Barge-In

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<div align="center">

**Made with 🎙️ + ☕ by Shiv**

*If E.V. saved you from context-switching, give the repo a ⭐*

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:16213e,50:1a1a2e,100:0d1117&height=120&section=footer" width="100%"/>

</div>
