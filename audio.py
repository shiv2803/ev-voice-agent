"""Mic/speaker I/O via sounddevice (PortAudio bindings that don't need a C
compiler on Windows — unlike PyAudio, which needs Microsoft Visual C++ Build
Tools to build its native extension from source when no prebuilt wheel
matches your Python version).

Voice Agent API audio encoding is `audio/pcm`: 16-bit signed little-endian
PCM at 24 kHz, mono. See:
https://www.assemblyai.com/docs/voice-agents/voice-agent-api/audio-format
"""

from queue import Queue

import sounddevice as sd

SAMPLE_RATE = 24000
CHUNK_SIZE = 1200  # 50ms at 24kHz 16-bit mono, per the docs' recommendation


class Mic:
    def __init__(self):
        self.queue: "Queue[bytes]" = Queue()
        self._stream = None

    def start(self):
        def callback(indata, frames, time_info, status):
            if status:
                print(f"[mic] {status}")
            self.queue.put(bytes(indata))

        self._stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=CHUNK_SIZE,
            callback=callback,
        )
        self._stream.start()

    def stop(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None


class Speaker:
    def __init__(self):
        self._stream = self._open()

    def _open(self):
        stream = sd.RawOutputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
        )
        stream.start()
        return stream

    def play(self, audio_bytes: bytes):
        self._stream.write(audio_bytes)

    def flush_and_restart(self):
        """Discard queued playback and reopen the stream.

        Called on barge-in (the user interrupts the agent) so playback
        doesn't keep talking over them.
        """
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            pass
        self._stream = self._open()

    def close(self):
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            pass
