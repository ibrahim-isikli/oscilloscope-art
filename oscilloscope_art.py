#!/usr/bin/env python3
"""
Oscilloscope Art - Shapes & Emoji
===================================
Draws geometric shapes on an oscilloscope screen using XY mode.

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

SAMPLE_RATE = 44100

# --- Pick which shapes to generate ---
SHAPES = ["heart", "star", "smiley"]


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


def heart_xy(n=1024):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x = 16 * np.sin(t) ** 3
    y = 13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t)
    return normalize(x), normalize(y)


def star_xy(n=1024, spikes=5):
    angles = np.linspace(0, 2 * np.pi, 2 * spikes, endpoint=False) - np.pi / 2
    radii = np.tile([1.0, 0.38], spikes)
    vx = radii * np.cos(angles)
    vy = radii * np.sin(angles)
    vx = np.append(vx, vx[0])
    vy = np.append(vy, vy[0])
    return arc_resample(normalize(vx), normalize(vy), n)


def smiley_xy(n=2048):
    t = np.linspace(0, 2 * np.pi, 400, endpoint=False)

    # face circle
    fx, fy = np.cos(t), np.sin(t)

    # left eye
    lx = -0.32 + 0.10 * np.cos(t)
    ly =  0.30 + 0.10 * np.sin(t)

    # right eye
    rx =  0.32 + 0.10 * np.cos(t)
    ry =  0.30 + 0.10 * np.sin(t)

    # smile arc (bottom half)
    ts = np.linspace(np.pi + 0.35, 2 * np.pi - 0.35, 300)
    sx = 0.52 * np.cos(ts)
    sy = 0.52 * np.sin(ts) + 0.10

    def bridge(ax, ay, bx, by, steps=8):
        return np.linspace(ax, bx, steps), np.linspace(ay, by, steps)

    bx1, by1 = bridge(fx[-1], fy[-1], lx[0], ly[0])
    bx2, by2 = bridge(lx[-1], ly[-1], rx[0], ry[0])
    bx3, by3 = bridge(rx[-1], ry[-1], sx[0], sy[0])

    all_x = np.concatenate([fx, bx1, lx, bx2, rx, bx3, sx])
    all_y = np.concatenate([fy, by1, ly, by2, ry, by3, sy])

    return arc_resample(normalize(all_x), normalize(all_y), n)


SHAPE_FN = {
    "heart":  heart_xy,
    "star":   star_xy,
    "smiley": smiley_xy,
}


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
    for name in SHAPES:
        if name not in SHAPE_FN:
            print(f"Unknown shape: {name}. Choose from: {list(SHAPE_FN)}")
            continue
        print(f"Generating '{name}'...")
        x, y = SHAPE_FN[name]()
        save_wav(x, y, f"{name}.wav")
    print("Done! Play the WAV files while your oscilloscope is in XY mode.")
