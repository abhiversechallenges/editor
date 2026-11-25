import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "work" / "scene_plan.json"
SCENES_DIR = ROOT / "src" / "generated" / "scenes"


def main() -> None:
    if not PLAN_PATH.exists():
        raise SystemExit("Missing work/scene_plan.json")
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    scenes = plan.get("scenes", [])
    if not scenes:
        raise SystemExit("Plan contains 0 scenes.")
    for sc in scenes:
        f = SCENES_DIR / f"{sc['componentName']}.tsx"
        if not f.exists():
            raise SystemExit(f"Missing scene file: {f.name}")
        txt = f.read_text(encoding="utf-8")
        for bad in ("<div", "<span", "useFrame", "useEffect", "useState", "from 'three'"):
            if bad in txt:
                raise SystemExit(f"Scene {f.name} contains forbidden token: {bad}")
    print(f"[validate_scenes] PASSED: All {len(scenes)} blueprint scenes verified.")


if __name__ == "__main__":
    main()
