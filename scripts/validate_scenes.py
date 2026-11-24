import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "work" / "scene_plan.json"
SCENES_DIR = ROOT / "src" / "generated" / "scenes"
TIMELINE_PATH = ROOT / "src" / "generated" / "GeneratedTimeline.tsx"

FORBIDDEN_3D_TOKENS = ("<Text", "<Html", "<Sequence")


def audit_plan(plan: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    scenes = plan.get("scenes") or []
    if not scenes:
        return ["scene_plan.json has 0 scenes."]

    seen_concepts: set[str] = set()
    for idx, sc in enumerate(scenes):
        concept = sc.get("visualConcept", "").strip().lower()
        if concept in seen_concepts:
            errors.append(f"Duplicate visualConcept detected: {concept}")
        seen_concepts.add(concept)

        if idx > 0 and abs(float(sc["startSec"]) - float(scenes[idx - 1]["endSec"])) > 0.01:
            errors.append(f"Timeline discontinuity between {scenes[idx-1]['id']} and {sc['id']}.")

        beats = sc.get("beats") or []
        if len(beats) < 2:
            errors.append(f"{sc['id']} has fewer than 2 micro-beats (visual hold too static).")

        for b in beats:
            b_dur = float(b["endSec"]) - float(b["startSec"])
            if b_dur > 5.5:
                errors.append(f"{b['id']} hold duration {b_dur:.2f}s exceeds 5.5s max beat pace.")

        cname = sc.get("componentName")
        if not (SCENES_DIR / f"{cname}.tsx").exists():
            errors.append(f"Missing generated scene component: {cname}.tsx")

    subtitles = plan.get("subtitleChunks") or []
    for i in range(len(subtitles) - 1):
        if float(subtitles[i]["endSec"]) > float(subtitles[i + 1]["startSec"]):
            errors.append(f"Overlapping subtitleChunks at index {i} ({subtitles[i]['endSec']} > {subtitles[i+1]['startSec']}).")

    return errors


def audit_3d_files() -> List[str]:
    errors: List[str] = []
    files = list(SCENES_DIR.glob("Scene_*.tsx")) + [TIMELINE_PATH]
    for f in files:
        if not f.exists():
            continue
        txt = f.read_text(encoding="utf-8")
        for m in FORBIDDEN_3D_TOKENS:
            if m in txt:
                errors.append(f"Forbidden token '{m}' found inside {f.name}")
    return errors


def main() -> None:
    if not PLAN_PATH.exists():
        raise SystemExit("Missing work/scene_plan.json")
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    errs = audit_plan(plan) + audit_3d_files()
    if errs:
        raise SystemExit("[validate_scenes] FAILED:\n - " + "\n - ".join(errs))
    total_beats = sum(len(s.get("beats", [])) for s in plan["scenes"])
    print(f"[validate_scenes] PASSED: {len(plan['scenes'])} scenes, {total_beats} visual beats, zero overlaps.")


if __name__ == "__main__":
    main()
