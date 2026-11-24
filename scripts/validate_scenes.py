import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "work" / "scene_plan.json"
SCENES_DIR = ROOT / "src" / "generated" / "scenes"
TIMELINE_PATH = ROOT / "src" / "generated" / "GeneratedTimeline.tsx"

FORBIDDEN_TOKENS = ("<div", "<span", "useFrame", "useEffect", "useState", "from 'three'", 'from "three"')


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

        if idx > 0:
            prev = scenes[idx - 1]
            if abs(float(sc["startSec"]) - float(prev["endSec"])) > 0.01:
                errors.append(f"Timeline gap between {prev['id']} and {sc['id']}.")
            if sc["backdropTheme"] == prev["backdropTheme"] and sc["backdropTheme"] != "black_title_card":
                errors.append(f"Consecutive identical backdropTheme '{sc['backdropTheme']}' at {sc['id']}.")

        dur = float(sc["endSec"]) - float(sc["startSec"])
        if dur > 9.5:
            errors.append(f"{sc['id']} duration {dur:.2f}s exceeds 9.5s max hold.")

        cname = sc.get("componentName")
        if not (SCENES_DIR / f"{cname}.tsx").exists():
            errors.append(f"Missing generated scene component: {cname}.tsx")

    return errors


def audit_source_files() -> List[str]:
    errors: List[str] = []
    for f in list(SCENES_DIR.glob("Scene_*.tsx")):
        txt = f.read_text(encoding="utf-8")
        for tok in FORBIDDEN_TOKENS:
            if tok in txt:
                errors.append(f"Forbidden token '{tok}' inside {f.name}")
    return errors


def main() -> None:
    if not PLAN_PATH.exists():
        raise SystemExit("Missing work/scene_plan.json")
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    errs = audit_plan(plan) + audit_source_files()
    if errs:
        raise SystemExit("[validate_scenes] FAILED:\n - " + "\n - ".join(errs))
    print(f"[validate_scenes] PASSED: {len(plan['scenes'])} unique continuous 2D cartoon scenes.")


if __name__ == "__main__":
    main()
