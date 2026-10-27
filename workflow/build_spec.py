"""Paste workflow/intake_estimator.py into the Custom Python blocks of workflow/intake-plate.json.

Run after any edit to intake_estimator.py: .venv-app/Scripts/python workflow/build_spec.py
`--check` exits 1 if the spec is out of sync (no write).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE / "intake-plate.json"
SRC = HERE / "intake_estimator.py"


def build():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    code = SRC.read_text(encoding="utf-8")
    in_sync = True
    for block in spec["dynamic_blocks_definitions"]:  # MenuSplit + IntakeEstimator share the file
        in_sync &= block["code"]["run_function_code"] == code
        block["code"]["run_function_code"] = code
    return spec, in_sync


if __name__ == "__main__":
    spec, in_sync = build()
    if "--check" in sys.argv:
        print("in sync" if in_sync else "OUT OF SYNC: run workflow/build_spec.py")
        sys.exit(0 if in_sync else 1)
    SPEC.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {SPEC.name} ({'unchanged' if in_sync else 'code updated'})")
