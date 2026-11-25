import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "work" / "scene_plan.json"


def main() -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    fps = int(plan["fps"])
    total_frames = max(60, int(round(float(plan["totalDurationSec"]) * fps)))

    force = os.environ.get("FORCE_WORKERS", "auto").strip().lower()
    if force.isdigit():
        workers = int(force)
    else:
        if total_frames <= 1800:
            workers = 4
        elif total_frames <= 5400:
            workers = 8
        elif total_frames <= 13500:
            workers = 14
        else:
            workers = 20

    workers = min(workers, total_frames)
    chunk_size = math.ceil(total_frames / workers)

    chunks = []
    for idx in range(workers):
        start_f = idx * chunk_size
        end_f = min(total_frames - 1, (idx + 1) * chunk_size - 1)
        if start_f <= end_f:
            chunks.append({"idx": idx, "start": start_f, "end": end_f})

    chunks_json = json.dumps(chunks)
    print(f"[plan_chunks] total_frames={total_frames}, parallel_workers={len(chunks)}")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"total_frames={total_frames}\n")
            f.write(f"worker_count={len(chunks)}\n")
            f.write(f"chunks_json={chunks_json}\n")


if __name__ == "__main__":
    main()
