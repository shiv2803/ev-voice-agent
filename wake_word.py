"""Local, always-on wake-word listener using Picovoice Porcupine.

Runs entirely offline: no audio leaves your machine, and no AssemblyAI
credits are spent, until the wake word actually fires. Porcupine (unlike
openWakeWord) can generate a custom keyword straight from typed text --
no recordings, no GPU training -- which is how you get a literal "Hey E.V."
trigger instead of a pretrained stand-in phrase.

One-time setup (you do this yourself -- it needs your own free account):
1. Create a free account at https://console.picovoice.ai/
2. Copy your AccessKey from the console's account page into
   PICOVOICE_ACCESS_KEY in .env.
3. Console -> Porcupine -> Create Wake Word -> type "Hey E.V." (or a
   variant the console rates well -- it shows a training-quality estimate
   and will suggest alternatives if the phrase is too short/ambiguous) ->
   pick Windows as the platform -> download the .ppn file.
4. Put that .ppn file somewhere in this project (e.g. a `wake_words/`
   folder) and point PORCUPINE_KEYWORD_PATH in .env at its exact path.

Free tier covers personal/hobby use. If these aren't configured yet,
agent.py falls back to always-on listening rather than crashing.
"""

import numpy as np
import sounddevice as sd
import pvporcupine


class WakeWordDetector:
    def __init__(self, access_key: str, keyword_path: str):
        if not access_key:
            raise RuntimeError(
                "PICOVOICE_ACCESS_KEY is not set. Get a free one at "
                "https://console.picovoice.ai/ and add it to .env."
            )
        if not keyword_path:
            raise RuntimeError(
                "PORCUPINE_KEYWORD_PATH is not set. Generate a custom "
                'keyword file for "Hey E.V." at https://console.picovoice.ai/ '
                "(Porcupine -> Create Wake Word), then point this at the "
                "downloaded .ppn file in .env."
            )

        # pvporcupine.create() raises its own clear error if the path is
        # missing/invalid/wrong-platform -- let that surface rather than
        # duplicating its validation here.
        self.porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=[keyword_path],
        )

    def wait_for_trigger(self):
        """Blocks until the wake word is heard, then returns."""
        triggered = {"value": False}

        def callback(indata, frames, time_info, status):
            if triggered["value"]:
                return
            pcm = np.frombuffer(bytes(indata), dtype=np.int16)
            if self.porcupine.process(pcm) >= 0:
                triggered["value"] = True

        with sd.RawInputStream(
            samplerate=self.porcupine.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self.porcupine.frame_length,
            callback=callback,
        ):
            while not triggered["value"]:
                sd.sleep(50)

    def close(self):
        self.porcupine.delete()
