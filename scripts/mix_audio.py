import json
import os
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = ROOT / "work"
SFX_DIR = ROOT / "public" / "audio" / "sfx"
SAMPLE_RATE = 48000


def lowpass(signal: np.ndarray, cutoff_hz: float, order: int = 4) -> np.ndarray:
    return sosfilt(butter(order, cutoff_hz, btype="low", fs=SAMPLE_RATE, output="sos"), signal)


def bandpass(signal: np.ndarray, low: float, high: float) -> np.ndarray:
    return sosfilt(butter(3, [low, high], btype="band", fs=SAMPLE_RATE, output="sos"), signal)


def synthesize_calm_underscore(n_samples: int, bpm: float) -> np.ndarray:
    t = np.arange(n_samples, dtype=np.float64) / SAMPLE_RATE
    bar_sec = (60.0 / max(75.0, min(125.0, bpm))) * 4.0
    chords = [
        [146.83, 220.00, 261.63, 329.63],
        [116.54, 174.61, 220.00, 293.66],
        [130.81, 196.00, 246.94, 293.66],
        [110.00, 164.81, 220.00, 261.63],
    ]
    bar_idx = (t / bar_sec).astype(int) % len(chords)
    env = np.sin(np.pi * np.clip((t % bar_sec) / bar_sec, 0.0, 1.0)) ** 0.5
    left, right = np.zeros(n_samples), np.zeros(n_samples)
    for c_i, freqs in enumerate(chords):
        mask = (bar_idx == c_i).astype(np.float64)
        sl, sr_sig = np.zeros(n_samples), np.zeros(n_samples)
        for v_i, freq in enumerate(freqs):
            sl += 0.22 * np.sin(2.0 * np.pi * freq * t)
            sr_sig += 0.22 * np.sin(2.0 * np.pi * freq * (1.002 if v_i % 2 == 0 else 0.998) * t + 0.35)
        left += mask * env * sl
        right += mask * env * sr_sig

    beat_period = 60.0 / bpm
    pulse = np.sin(2.0 * np.pi * 146.83 * t) * np.exp(-((t % beat_period) / beat_period) * 14.0) * 0.10
    stereo = np.column_stack([lowpass(left + pulse, 880.0), lowpass(right + pulse, 880.0)])
    stereo = stereo / (float(np.max(np.abs(stereo))) + 1e-9)
    fade_in, fade_out = min(n_samples, int(1.5 * SAMPLE_RATE)), min(n_samples, int(2.0 * SAMPLE_RATE))
    if fade_in > 0:
        stereo[:fade_in] *= np.linspace(0.0, 1.0, fade_in)[:, None]
    if fade_out > 0:
        stereo[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)[:, None]
    return stereo


def load_or_synthesize_sfx() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(42)
    nw = int(0.30 * SAMPLE_RATE)
    w = bandpass(rng.normal(0.0, 1.0, nw), 320.0, 2600.0) * (np.sin(np.pi * (np.arange(nw) / SAMPLE_RATE) / 0.30) ** 1.5)
    whoosh = np.column_stack([w, w * 0.94]) / (np.max(np.abs(w)) + 1e-9)

    npop = int(0.10 * SAMPLE_RATE)
    tp = np.arange(npop) / SAMPLE_RATE
    p = np.sin(2.0 * np.pi * np.cumsum(420.0 + 520.0 * (1.0 - np.exp(-tp * 40.0))) / SAMPLE_RATE) * np.exp(-tp * 34.0)
    pop = np.column_stack([p, p]) / (np.max(np.abs(p)) + 1e-9)

    nt = int(0.06 * SAMPLE_RATE)
    tt = np.arange(nt) / SAMPLE_RATE
    tk = np.sin(2.0 * np.pi * 1950.0 * tt) * np.exp(-tt * 85.0)
    tick = np.column_stack([tk, tk]) / (np.max(np.abs(tk)) + 1e-9)

    na = int(0.24 * SAMPLE_RATE)
    ta = np.arange(na) / SAMPLE_RATE
    al = (np.sin(2.0 * np.pi * 1180.0 * ta) + 0.5 * np.sin(2.0 * np.pi * 1760.0 * ta)) * np.exp(-ta * 16.0)
    alert = np.column_stack([al, al]) / (np.max(np.abs(al)) + 1e-9)

    ni = int(0.45 * SAMPLE_RATE)
    ti = np.arange(ni) / SAMPLE_RATE
    im = np.sin(2.0 * np.pi * np.cumsum(100.0 * np.exp(-ti * 4.8) + 36.0) / SAMPLE_RATE) * np.exp(-ti * 5.8) * np.minimum(1.0, ti / 0.01)
    impact = np.column_stack([im, im]) / (np.max(np.abs(im)) + 1e-9)

    bank = {"whoosh": whoosh * 0.14, "pop": pop * 0.16, "tick": tick * 0.12, "alert": alert * 0.14, "impact": impact * 0.22}
    for name in list(bank.keys()):
        custom_wav = SFX_DIR / f"{name}.wav"
        if custom_wav.exists():
            data, sr = sf.read(str(custom_wav), dtype="float64")
            if sr == SAMPLE_RATE:
                if data.ndim == 1:
                    data = np.column_stack([data, data])
                bank[name] = (data / (float(np.max(np.abs(data))) + 1e-9)) * 0.18
    return bank


def place_sfx(mix: np.ndarray, snd: np.ndarray, sec: float) -> None:
    s = max(0, int(sec * SAMPLE_RATE))
    e = min(len(mix), s + len(snd))
    if e > s:
        mix[s:e] += snd[: e - s]


def main() -> None:
    plan = json.loads((WORK_DIR / "scene_plan.json").read_text(encoding="utf-8"))
    vo, _ = sf.read(str(WORK_DIR / "clean_voiceover.wav"), dtype="float64")
    if vo.ndim > 1:
        vo = np.mean(vo, axis=1)

    n_samples = len(vo)
    vo_stereo = np.column_stack([vo, vo])
    include_bgm = os.environ.get("INCLUDE_BGM", "true").lower() == "true"

    if include_bgm:
        smooth_env = lowpass(np.abs(vo), 3.0)
        speech_active = np.clip(smooth_env / (np.percentile(smooth_env, 90) + 1e-6), 0.0, 1.0)
        duck_gain = 0.085 - 0.048 * speech_active
        mix = vo_stereo * 0.92 + synthesize_calm_underscore(n_samples, float(plan.get("bpm", 105.0))) * duck_gain[:, None]
    else:
        mix = vo_stereo * 0.94

    bank = load_or_synthesize_sfx()
    for sc in plan.get("scenes", []):
        place_sfx(mix, bank.get(sc.get("sfx", "whoosh"), bank["whoosh"]), float(sc["startSec"]))
        if sc.get("statCounter"):
            place_sfx(mix, bank["pop"], float(sc["startSec"]) + float(sc["statCounter"].get("triggerSec", 0.15)))
        if sc.get("stampText"):
            place_sfx(mix, bank["alert"], float(sc["startSec"]) + float(sc.get("stampTriggerSec", 0.65)))

    for idx, p_sec in enumerate(plan.get("emphasisPeaksSec", [])):
        place_sfx(mix, bank["impact" if idx % 5 == 0 else "tick"], float(p_sec))

    mix = np.tanh(mix * 0.95)
    master_m4a, tmp_wav = WORK_DIR / "master_audio.m4a", WORK_DIR / "temp_master.wav"
    sf.write(str(tmp_wav), mix, SAMPLE_RATE, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(tmp_wav), "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE), str(master_m4a)], check=True)
    tmp_wav.unlink(missing_ok=True)
    print(f"[mix_audio] Master mix complete: {n_samples / SAMPLE_RATE:.2f}s (BGM={include_bgm}).")


if __name__ == "__main__":
    main()
