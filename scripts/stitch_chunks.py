import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNKS_DIR = ROOT / "chunks"
WORK_DIR = ROOT / "work"
OUT_DIR = ROOT / "out"


def chunk_index(p: Path) -> int:
    m = re.search(r"chunk_(\d+)\.mp4$", p.name)
    return int(m.group(1)) if m else 999999


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chunk_files = sorted(CHUNKS_DIR.rglob("chunk_*.mp4"), key=chunk_index)
    if not chunk_files:
        raise FileNotFoundError("No rendered chunk_*.mp4 files found in chunks/.")

    list_file = WORK_DIR / "chunks.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for cf in chunk_files:
            f.write(f"file '{cf.resolve().as_posix()}'\n")

    master_audio = WORK_DIR / "master_audio.m4a"
    final_mp4 = OUT_DIR / "final_video.mp4"

    print(f"[stitch_chunks] Joining {len(chunk_files)} chunk(s) + master_audio.m4a -> {final_mp4}")
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-i", str(master_audio),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "copy",
            "-movflags", "+faststart",
            "-shortest",
            str(final_mp4),
        ],
        check=True,
    )
    print(f"[stitch_chunks] SUCCESS! Exported {final_mp4} ({final_mp4.stat().st_size / (1024*1024):.1f} MB)")


if __name__ == "__main__":
    main()
