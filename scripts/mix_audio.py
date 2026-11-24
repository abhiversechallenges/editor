import json
import os
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = ROOT / "work"
SAMPLE_RATE = 48000


def lowpass(signal: np.ndarray, cutoff_hz: float, order: int = 4) -> np.ndarray:
    sos = butter(order, cutoff_hz, btype="low", fs=SAMPLE_RATE, output="sos")
    return sosfilt(sos, signal)


def bandpass(signal: np.ndarray, low_hz: float, high_hz: float, order: int = 3) -> np.ndarray:
    sos = butter(order, [low_hz, high_hz], btype="band", fs=SAMPLE_RATE, output="sos")
    return sosfilt(sos, signal)


def synthesize_underscore_bgm(n_samples: int, bpm: float) -> np.ndarray:
    t = np.arange(n_samples, dtype=np.float64) / SAMPLE_RATE
    bar_sec = (60.0 / max(75.0, min(125.0, bpm))) * 4.0
    chords = [
        [146.83, 220.00, 261.63, 329.63],
        [116.54, 174.61, 220.00, 293.66],
        [130.81, 196.00, 246.94, 293.66],
        [110.00, 164.81, 220.00, 261.63],
    ]
    bar_idx = (t / bar_sec).astype(int) % len(chords)
    bar_phase = (t % bar_sec) / bar_sec
    env = np.sin(np.pi * np.clip(bar_phase, 0.0, 1.0)) ** 0.45

    left = np.zeros(n_samples, dtype=np.float64)
    right = np.zeros(n_samples, dtype=np.float64)
    for c_i, freqs in enumerate(chords):
        mask = (bar_idx == c_i).astype(np.float64)
        sig_l = np.zeros(n_samples, dtype=np.float64)
        sig_r = np.zeros(n_samples, dtype=np.float64)
        for v_i, freq in enumerate(freqs):
            detune = 1.002 if v_i % 2 == 0 else 0.998
            sig_l += 0.22 * np.sin(2.0 * np.pi * freq * t)
            sig_r += 0.22 * np.sin(2.0 * np.pi * freq * detune * t + 0.4)
        left += mask * env * sig_l
        right += mask * env * sig_r

    beat_period = 60.0 / bpm
    pulse = np.sin(2.0 * np.pi * 196.0 * t) * np.exp(-((t % beat_period) / beat_period) * 12.0) * 0.14
    left = lowpass(left + pulse, 1050.0)
    right = lowpass(right + pulse, 1050.0)
    stereo = np.column_stack([left, right])
    stereo = stereo / (float(np.max(np.abs(stereo))) + 1e-9)

    fade_in = min(n_samples, int(1.5 * SAMPLE_RATE))
    fade_out = min(n_samples, int(2.0 * SAMPLE_RATE))
    if fade_in > 0:
        stereo[:fade_in] *= np.linspace(0.0, 1.0, fade_in)[:, None]
    if fade_out > 0:
        stereo[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)[:, None]
    return stereo


def make_sfx_bank() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(17)

    # 1. Smooth slide whoosh
    nw = int(0.32 * SAMPLE_RATE)
    tw = np.arange(nw) / SAMPLE_RATE
    w = bandpass(rng.normal(0.0, 1.0, nw), 320.0, 2400.0) * (np.sin(np.pi * tw / 0.32) ** 1.5)
    whoosh = np.column_stack([w, w * 0.94]) / (float(np.max(np.abs(w))) + 1e-9)

    # 2. Cartoon pop snap
    npop = int(0.11 * SAMPLE_RATE)
    tp = np.arange(npop) / SAMPLE_RATE
    fp = 360.0 + 480.0 * (1.0 - np.exp(-tp * 38.0))
    p = np.sin(2.0 * np.pi * np.cumsum(fp) / SAMPLE_RATE) * np.exp(-tp * 32.0)
    pop_snap = np.column_stack([p, p]) / (float(np.max(np.abs(p))) + 1e-9)

    # 3. Marker / highlighter swipe
    nm = int(0.28 * SAMPLE_RATE)
    tm = np.arange(nm) / SAMPLE_RATE
    m = bandpass(rng.normal(0.0, 1.0, nm), 1200.0, 4200.0) * (np.sin(np.pi * tm / 0.28) ** 1.2)
    marker_swipe = np.column_stack([m, m]) / (float(np.max(np.abs(m))) + 1e-9)

    # 4. Dramatic sub impact
    ns = int(0.45 * SAMPLE_RATE)
    ts = np.arange(ns) / SAMPLE_RATE
    fs = 105.0 * np.exp(-ts * 4.5) + 40.0
    s = np.sin(2.0 * np.pi * np.cumsum(fs) / SAMPLE_RATE) * np.exp(-ts * 5.5) * np.minimum(1.0, ts / 0.012)
    sub_impact = np.column_stack([s, s]) / (float(np.max(np.abs(s))) + 1e-9)

    # 5. Crisp tick
    nt = int(0.07 * SAMPLE_RATE)
    tt = np.arange(nt) / SAMPLE_RATE
    tk = np.sin(2.0 * np.pi * 1600.0 * tt) * np.exp(-tt * 70.0)
    tick = np.column_stack([tk, tk]) / (float(np.max(np.abs(tk))) + 1e-9)

    return {
        "whoosh": whoosh * 0.14,
        "pop_snap": pop_snap * 0.16,
        "marker_swipe": marker_swipe * 0.12,
        "sub_impact": sub_impact * 0.20,
        "tick": tick * 0.11,
    }


def main() -> None:
    plan = json.loads((WORK_DIR / "scene_plan.json").read_text(encoding="utf-8"))
    vo_data, sr = sf.read(str(WORK_DIR / "clean_voiceover.wav"), dtype="float64")
    if sr != SAMPLE_RATE:
        raise RuntimeError(f"Expected 48000 Hz clean_voiceover.wav, got {sr}")
    vo_mono = np.mean(vo_data, axis=1) if vo_data.ndim > 1 else vo_data

    n_samples = len(vo_mono)
    vo_stereo = np.column_stack([vo_mono, vo_mono])

    include_bgm = os.environ.get("INCLUDE_BGM", "true").lower() == "true"
    if include_bgm:
        abs_vo = np.abs(vo_mono)
        smooth_env = lowpass(abs_vo, 3.0)
        speech_active = np.clip(smooth_env / (np.percentile(smooth_env, 90) + 1e-6), 0.0, 1.0)
        duck_gain = 0.085 - 0.042 * speech_active
        bgm_stereo = synthesize_underscore_bgm(n_samples, float(plan.get("bpm", 104.0)))
        mix = vo_stereo * 0.92 + bgm_stereo * duck_gain[:, None]
    else:
        mix = vo_stereo * 0.94

    sfx_bank = make_sfx_bank()
    for sc in plan["scenes"]:
        cue = sc.get("sfx", "pop_snap")
        snd = sfx_bank.get(cue, sfx_bank["pop_snap"])
        start_idx = max(0, int(float(sc["startSec"]) * SAMPLE_RATE))
        end_idx = min(n_samples, start_idx + len(snd))
        if end_idx > start_idx:
            mix[start_idx:end_idx] += snd[: end_idx - start_idx]

    mix = np.tanh(mix * 0.95)
    master_wav = WORK_DIR / "master_audio.wav"
    master_m4a = WORK_DIR / "master_audio.m4a"
    sf.write(str(master_wav), mix, SAMPLE_RATE, subtype="PCM_16")
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(master_wav),
            "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE),
            str(master_m4a),
        ],
        check=True,
    )
    master_wav.unlink(missing_ok=True)
    print(f"[mix_audio] Built master_audio.m4a ({n_samples / SAMPLE_RATE:.2f}s, include_bgm={include_bgm}).")


if __name__ == "__main__":
    main()
