#!/usr/bin/env python3
"""
Oscilloscope Art - Lyrics
==========================
Scrolls song lyrics phrase by phrase on an oscilloscope in XY mode.

Requirements:
    pip install matplotlib numpy

Hardware:
    - Oscilloscope with XY mode
    - 3.5mm stereo AUX cable
    - Left channel  -> CH1 (X axis)
    - Right channel -> CH2 (Y axis)

Oscilloscope settings:
    Format: XY | CH1 & CH2: 500 mV/div | Persistence: Infinite
"""

import numpy as np
import wave
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

SAMPLE_RATE = 44100

# ---------------------------------------------------------------
# Edit LYRICS below. Each item is either:
#   "phrase"           -> shown for SECONDS_PER_LINE seconds
#   ("phrase", 2.5)    -> shown for 2.5 seconds (custom timing)
#
# Keep phrases short (2-4 words) for best readability.
# ---------------------------------------------------------------

LYRICS = [
    ("Flashing", 2.5),
    ("lights",   2.5),
    ("Flashing", 2.5),
    ("lights",   2.5),
    ("Flashing", 2.5),
    ("lights",   2.5),
    ("Flashing", 2.5),
    ("lights",   2.5),
    "She don't",
    "believe",
    "in shootin'",
    "stars",
    "But she",
    "believe",
    "shoes and cars",
    "Wood floors",
    "new apartment",
    "Couture",
    "departments",
]

SECONDS_PER_LINE = 1.5   # default duration for lines without custom timing


def normalize(arr, scale=0.90):
    lo, hi = arr.min(), arr.max()
    if hi == lo:
        return np.zeros_like(arr)
    return (2 * (arr - lo) / (hi - lo) - 1) * scale


def arc_resample(x, y, n):
    dx, dy = np.diff(x), np.diff(y)
    cum = np.concatenate([[0], np.cumsum(np.hypot(dx, dy))])
    if cum[-1] == 0:
        return np.zeros(n), np.zeros(n)
    t = np.linspace(0, cum[-1], n)
    return np.interp(t, cum, x), np.interp(t, cum, y)


def auto_n(text):
    return int(np.clip(len(text) * 220, 768, 2048))


def text_xy(text, n=None):
    if n is None:
        n = auto_n(text)
    fp = FontProperties(family="DejaVu Sans", weight="bold")
    tp = TextPath((0, 0), text, size=10, prop=fp)
    polys = tp.to_polygons()

    if not polys:
        raise RuntimeError("Could not render text: " + repr(text))

    xs, ys = [], []
    for i, p in enumerate(polys):
        if len(p) < 2:
            continue
        closed = np.vstack([p, p[0]])
        xs.append(closed[:, 0])
        ys.append(closed[:, 1])
        if i < len(polys) - 1:
            nxt = polys[i + 1]
            bx = np.linspace(closed[-1, 0], nxt[0, 0], 6)
            by = np.linspace(closed[-1, 1], nxt[0, 1], 6)
            xs.append(bx)
            ys.append(by)

    x = normalize(np.concatenate(xs))
    y = normalize(np.concatenate(ys))
    return arc_resample(x, y, n)


def xy_to_samples(x, y, duration):
    n_samples = int(duration * SAMPLE_RATE)
    reps = -(-n_samples // len(x))
    xf = np.tile(x, reps)[:n_samples]
    yf = np.tile(y, reps)[:n_samples]
    return xf, yf


def build_lyrics_wav(phrases, default_dur, path):
    BLANK = int(0.25 * SAMPLE_RATE)   # short blank between phrases

    all_x, all_y = [], []

    for i, item in enumerate(phrases):
        phrase, dur = (item[0], item[1]) if isinstance(item, tuple) else (item, default_dur)
        print(f"  [{i+1}/{len(phrases)}] {phrase!r}  ({dur}s)")
        x, y = text_xy(phrase)
        xf, yf = xy_to_samples(x, y, dur)
        all_x.append(xf)
        all_y.append(yf)
        all_x.append(np.zeros(BLANK))
        all_y.append(np.zeros(BLANK))

    x_full = np.concatenate(all_x)
    y_full = np.concatenate(all_y)

    xi = (np.clip(x_full, -1, 1) * 32767).astype(np.int16)
    yi = (np.clip(y_full, -1, 1) * 32767).astype(np.int16)
    stereo = np.empty(2 * len(xi), dtype=np.int16)
    stereo[0::2] = xi
    stereo[1::2] = yi

    with wave.open(path, "w") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(stereo.tobytes())

    total = len(x_full) / SAMPLE_RATE
    print(f"Saved: {path}  ({len(phrases)} phrases, {total:.1f}s total)")


if __name__ == "__main__":
    print("Generating lyrics WAV...")
    build_lyrics_wav(LYRICS, SECONDS_PER_LINE, "lyrics.wav")
    print("Done! Play lyrics.wav while your oscilloscope is in XY mode.")
