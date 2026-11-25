import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNKS_DIR, WORK_DIR, OUT_DIR = ROOT / "chunks", ROOT / "work", ROOT / "out"


def chunk_index(p: Path) -> int:
    m = re.search(r"chunk_(\d+)\.mp4$", p.name)
    return int(m.group(1)) if m else 999999


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chunks = sorted(CHUNKS_DIR.rglob("chunk_*.mp4"), key=chunk_index)
    if not chunks:
        raise FileNotFoundError("No rendered chunk_*.mp4 files found.")

    list_file = WORK_DIR / "chunks.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(f"file '{c.resolve().as_posix()}'\n")

    out_name = "final_short.mp4" if os.environ.get("VIDEO_FORMAT", "long_16_9").strip() == "short_9_16" else "final_video.mp4"
    final_mp4 = OUT_DIR / out_name
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
        "-f", "concat", "-safe", "0", "-i", str(list_file), "-i", str(WORK_DIR / "master_audio.m4a"),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", "-shortest", str(final_mp4)
    ], check=True)
    print(f"[stitch_chunks] SUCCESS! Exported {final_mp4} ({final_mp4.stat().st_size / (1024*1024):.1f} MB)")


if __name__ == "__main__":
    main()
