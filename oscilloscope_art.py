#!/usr/bin/env python3
"""
Oscilloscope Art - Text Generator
==================================
Draws text on an oscilloscope screen using XY mode.

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

# --- Change this to your name ---
YOUR_NAME = "ibrahim"


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


def text_xy(text, n=2048):
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


def save_wav(x, y, path, duration=10.0):
    n_samples = int(duration * SAMPLE_RATE)
    reps = -(-n_samples // len(x))
    xf = np.tile(x, reps)[:n_samples]
    yf = np.tile(y, reps)[:n_samples]

    xi = (np.clip(xf, -1, 1) * 32767).astype(np.int16)
    yi = (np.clip(yf, -1, 1) * 32767).astype(np.int16)

    stereo = np.empty(2 * n_samples, dtype=np.int16)
    stereo[0::2] = xi
    stereo[1::2] = yi

    with wave.open(path, "w") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(stereo.tobytes())

    hz = SAMPLE_RATE / len(x)
    print(f"Saved: {path}  ({hz:.1f} Hz refresh, {duration:.0f}s)")


if __name__ == "__main__":
    print(f"Generating '{YOUR_NAME}'...")
    x, y = text_xy(YOUR_NAME)
    save_wav(x, y, f"{YOUR_NAME}.wav")
    print("Done! Play the WAV file while your oscilloscope is in XY mode.")
