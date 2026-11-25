import json
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = ROOT / "work"
SAMPLE_RATE = 48000


def bandpass(signal: np.ndarray, low: float, high: float) -> np.ndarray:
    sos = butter(3, [low, high], btype="band", fs=SAMPLE_RATE, output="sos")
    return sosfilt(sos, signal)


def make_sfx_bank() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(42)
    nw = int(0.28 * SAMPLE_RATE)
    tw = np.arange(nw) / SAMPLE_RATE
    w = bandpass(rng.normal(0.0, 1.0, nw), 300.0, 2600.0) * (np.sin(np.pi * tw / 0.28) ** 1.5)
    whoosh = np.column_stack([w, w]) / (np.max(np.abs(w)) + 1e-9)

    np_snap = int(0.09 * SAMPLE_RATE)
    tp = np.arange(np_snap) / SAMPLE_RATE
    p = np.sin(2.0 * np.pi * 1800.0 * tp) * np.exp(-tp * 85.0)
    snap = np.column_stack([p, p]) / (np.max(np.abs(p)) + 1e-9)

    ns = int(0.42 * SAMPLE_RATE)
    ts = np.arange(ns) / SAMPLE_RATE
    fs = 95.0 * np.exp(-ts * 5.0) + 35.0
    s = np.sin(2.0 * np.pi * np.cumsum(fs) / SAMPLE_RATE) * np.exp(-ts * 6.0)
    sub = np.column_stack([s, s]) / (np.max(np.abs(s)) + 1e-9)

    return {
        "whoosh": whoosh * 0.15,
        "pop_snap": snap * 0.18,
        "marker_swipe": whoosh * 0.12,
        "sub_impact": sub * 0.22,
        "tick": snap * 0.12,
    }


def main() -> None:
    plan = json.loads((WORK_DIR / "scene_plan.json").read_text(encoding="utf-8"))
    vo, _ = sf.read(str(WORK_DIR / "clean_voiceover.wav"), dtype="float64")
    if vo.ndim > 1:
        vo = np.mean(vo, axis=1)

    n_samples = len(vo)
    mix = np.column_stack([vo, vo]) * 0.94
    sfx_bank = make_sfx_bank()

    for sc in plan.get("scenes", []):
        cue = sc.get("sfx", "pop_snap")
        snd = sfx_bank.get(cue, sfx_bank["pop_snap"])
        start_idx = max(0, int(float(sc["startSec"]) * SAMPLE_RATE))
        end_idx = min(n_samples, start_idx + len(snd))
        if end_idx > start_idx:
            mix[start_idx:end_idx] += snd[: end_idx - start_idx]

    mix = np.tanh(mix * 0.95)
    master_m4a = WORK_DIR / "master_audio.m4a"
    tmp_wav = WORK_DIR / "temp_master.wav"
    sf.write(str(tmp_wav), mix, SAMPLE_RATE, subtype="PCM_16")

    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(tmp_wav), "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE),
        str(master_m4a)
    ], check=True)
    tmp_wav.unlink(missing_ok=True)
    print(f"[mix_audio] Master audio built: {n_samples / SAMPLE_RATE:.2f}s.")


if __name__ == "__main__":
    main()
