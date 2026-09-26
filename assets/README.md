# Assets Folder

Place your demo GIFs here for the README animations.

## Required GIFs

| Filename | Duration | Content |
|----------|----------|---------|
| `demo.gif` | 30-60s | Full demo overview (terminal + audio visualization) |
| `architecture.gif` | 10-15s | Architecture diagram with animated flow |
| `briefing.gif` | 5-10s | Proactive briefing on launch |
| `bargein.gif` | 5-10s | Interrupting E.V. mid-sentence |
| `voice-switch.gif` | 5-10s | "Switch to a deeper voice" → reconnect |
| `screen-read.gif` | 5-10s | "What's on my screen?" → screenshot described |
| `tasks.gif` | 10-15s | Add/list/complete/delete tasks |
| `quickstart.gif` | 15-30s | Clone → setup → run flow |

## How to Record

**Windows:**
- **ScreenToGif** (free, open source) — best for GIFs
- **OBS Studio** → record MP4 → convert to GIF with `ffmpeg -i demo.mp4 -vf "fps=10,scale=800:-1:flags=lanczos" demo.gif`

**macOS:**
- **Kap** (free) — records directly to GIF
- **ScreenToGif** via Wine

**Linux:**
- **Peek** (free) — records to GIF
- **ScreenToGif** via Wine

## Tips

- Keep GIFs **under 10MB** each (GitHub limit)
- Use **800px width** max for README display
- **10-15 fps** is enough for terminal demos
- Record terminal at **120% zoom** for readability
- Show **both input (you speaking) and output (E.V. responding)**

## Quick ffmpeg Commands

```bash
# MP4 to GIF (optimized)
ffmpeg -i demo.mp4 -vf "fps=10,scale=800:-1:flags=lanczos,palettegen" palette.png
ffmpeg -i demo.mp4 -i palette.png -filter_complex "fps=10,scale=800:-1:flags=lanczos[x];[x][1:v]paletteuse" demo.gif

# Trim video first
ffmpeg -i demo.mp4 -ss 00:00:05 -t 30 -c copy demo-trimmed.mp4
```