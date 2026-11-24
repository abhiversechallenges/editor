import json
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


def synthesize_documentary_bgm(n_samples: int, bpm: float) -> np.ndarray:
    t = np.arange(n_samples, dtype=np.float64) / SAMPLE_RATE
    bar_sec = (60.0 / max(75.0, min(125.0, bpm))) * 4.0
    chords = [
        [130.81, 196.00, 233.08, 293.66],
        [103.83, 155.56, 196.00, 261.63],
        [87.31, 174.61, 207.65, 261.63],
        [98.00, 146.83, 196.00, 233.08],
    ]
    bar_idx = (t / bar_sec).astype(int) % len(chords)
    bar_phase = (t % bar_sec) / bar_sec
    env = np.sin(np.pi * np.clip(bar_phase, 0.0, 1.0)) ** 0.4

    left = np.zeros(n_samples, dtype=np.float64)
    right = np.zeros(n_samples, dtype=np.float64)
    for c_i, freqs in enumerate(chords):
        mask = (bar_idx == c_i).astype(np.float64)
        sig_l = np.zeros(n_samples, dtype=np.float64)
        sig_r = np.zeros(n_samples, dtype=np.float64)
        for v_i, freq in enumerate(freqs):
            detune = 1.0025 if v_i % 2 == 0 else 0.9975
            sig_l += 0.22 * np.sin(2.0 * np.pi * freq * t)
            sig_r += 0.22 * np.sin(2.0 * np.pi * freq * detune * t + 0.5)
        sub = 0.28 * np.sin(2.0 * np.pi * (freqs[0] * 0.5) * t)
        left += mask * env * (sig_l + sub)
        right += mask * env * (sig_r + sub)

    pulse_period = 60.0 / bpm
    pulse_env = np.exp(-((t % pulse_period) / pulse_period) * 6.5)
    pulse = np.sin(2.0 * np.pi * 65.0 * t) * pulse_env * 0.16

    left = lowpass(left + pulse, 920.0)
    right = lowpass(right + pulse, 920.0)
    stereo = np.column_stack([left, right])
    stereo = stereo / (float(np.max(np.abs(stereo))) + 1e-9)

    fade_in = min(n_samples, int(1.5 * SAMPLE_RATE))
    fade_out = min(n_samples, int(2.0 * SAMPLE_RATE))
    if fade_in > 0:
        stereo[:fade_in] *= np.linspace(0.0, 1.0, fade_in)[:, None]
    if fade_out > 0:
        stereo[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)[:, None]
    return stereo


def synthesize_glide_swell() -> np.ndarray:
    rng = np.random.default_rng(11)
    n = int(1.05 * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    env = np.sin(np.pi * t / 1.05) ** 1.8
    air = bandpass(rng.normal(0.0, 1.0, n), 160.0, 950.0) * env
    sub = np.sin(2.0 * np.pi * (54.0 - 16.0 * (t / 1.05)) * t) * env * 0.35
    sig = air * 0.65 + sub
    stereo = np.column_stack([sig, sig * 0.96])
    return stereo / (float(np.max(np.abs(stereo))) + 1e-9)


def synthesize_hud_tick() -> np.ndarray:
    n = int(0.08 * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    sig = np.sin(2.0 * np.pi * 1480.0 * t) * np.exp(-t * 60.0) * 0.6
    stereo = np.column_stack([sig, sig])
    return stereo / (float(np.max(np.abs(stereo))) + 1e-9)


def main() -> None:
    plan = json.loads((WORK_DIR / "scene_plan.json").read_text(encoding="utf-8"))
    vo_data, sr = sf.read(str(WORK_DIR / "clean_voiceover.wav"), dtype="float64")
    if sr != SAMPLE_RATE:
        raise RuntimeError(f"Expected 48000 Hz clean_voiceover.wav, got {sr}")
    vo_mono = np.mean(vo_data, axis=1) if vo_data.ndim > 1 else vo_data

    n_samples = len(vo_mono)
    vo_stereo = np.column_stack([vo_mono, vo_mono])

    abs_vo = np.abs(vo_mono)
    smooth_env = lowpass(abs_vo, 3.0)
    speech_active = np.clip(smooth_env / (np.percentile(smooth_env, 90) + 1e-6), 0.0, 1.0)
    duck_gain = 0.09 - 0.045 * speech_active

    bgm_stereo = synthesize_documentary_bgm(n_samples, float(plan.get("bpm", 102.0)))
    mix = vo_stereo * 0.92 + bgm_stereo * duck_gain[:, None]

    swell = synthesize_glide_swell() * 0.14
    hud_tick = synthesize_hud_tick() * 0.09

    for sc_idx, sc in enumerate(plan["scenes"]):
        if sc_idx > 0:
            s_idx = max(0, int((float(sc["startSec"]) - 0.5) * SAMPLE_RATE))
            e_idx = min(n_samples, s_idx + len(swell))
            if e_idx > s_idx:
                mix[s_idx:e_idx] += swell[: e_idx - s_idx]

        for b in sc.get("beats", []):
            t_idx = max(0, int(float(b["startSec"]) * SAMPLE_RATE))
            te_idx = min(n_samples, t_idx + len(hud_tick))
            if te_idx > t_idx:
                mix[t_idx:te_idx] += hud_tick[: te_idx - t_idx]

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
    print(f"[mix_audio] Built master_audio.m4a ({n_samples / SAMPLE_RATE:.2f}s).")


if __name__ == "__main__":
    main()
