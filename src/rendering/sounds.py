"""Three short cues. Silent when the mixer cannot start."""
from __future__ import annotations

import array
import math

_CUES = None


def cue_for(events, last_action) -> str | None:
    """One sound for an action: a bite, feeding, or a step."""
    kinds = {event.kind for event in events}
    if "hit" in kinds or "kill" in kinds:
        return "bite"
    food = getattr(last_action, "food_consumed", 0)
    if "depleted" in kinds or food:
        return "feed"
    if "step" in kinds:
        return "step"
    if last_action is not None and last_action.before != last_action.after:
        return "step"
    return None


def play_cues(events, last_action) -> None:
    name = cue_for(events, last_action)
    if name:
        play(name)


def play(name: str) -> None:
    cues = _load()
    sound = None if cues is None else cues.get(name)
    if sound is not None:
        sound.play()


def _load():
    global _CUES
    if _CUES is not None:
        return _CUES
    try:
        import pygame
        if pygame.mixer.get_init() is None:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        rate, _format, channels = pygame.mixer.get_init()
    except Exception:
        _CUES = {}
        return _CUES
    tones = {
        "step": _tone(rate, 150, 0.045, 0.22),
        "bite": _tone(rate, 420, 0.09, 0.34, sweep=-2400),
        "feed": _tone(rate, 660, 0.06, 0.2) + _tone(rate, 880, 0.07, 0.2),
    }
    _CUES = {name: pygame.mixer.Sound(buffer=_bytes(samples, channels)) for name, samples in tones.items()}
    return _CUES


def _tone(rate, freq, seconds, volume, sweep=0):
    count = max(1, int(rate * seconds))
    data = array.array("h")
    for index in range(count):
        t = index / rate
        env = 1 - index / count
        wave = math.sin(2 * math.pi * (freq * t + sweep * t * t / 2))
        data.append(int(max(-1, min(1, wave * env * volume)) * 32767))
    return data


def _bytes(samples, channels):
    if channels == 1:
        return samples.tobytes()
    stereo = array.array("h")
    for sample in samples:
        stereo.append(sample)
        stereo.append(sample)
    return stereo.tobytes()
