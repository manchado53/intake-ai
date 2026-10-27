"""Run the intake-plate Workflow on Roboflow's hosted serverless API and print the estimate.

  .venv-app/Scripts/python workflow/run_hosted.py IMG [IMG ...] [--inline] [--out DIR] [--raw DIR]
                                                   [--api-url URL] [--menu "a,b,c"]

Default calls the saved Workflow `intake-plate` in workspace `manchado53`; `--inline` sends
workflow/intake-plate.json instead (no saved Workflow needed). Prints {qr, estimate} per image,
saves the annotated JPEG to --out (default: system temp). `--raw DIR` also writes the full
response JSON per image with base64 images stripped. Key: ROBOFLOW_API_KEY from the repo .env.
"""
import argparse
import base64
import json
import os
import tempfile
import time
from pathlib import Path

from dotenv import dotenv_values
from inference_sdk import InferenceHTTPClient
from inference_sdk.http.errors import HTTPCallErrorError

HERE = Path(__file__).resolve().parent
WORKSPACE = "manchado53"
WORKFLOW_ID = "intake-plate"


def find_key():
    # The worktree has no .env; walk up to the main checkout's .env.
    for d in [HERE.parent, *HERE.parent.parents]:
        env = d / ".env"
        if env.exists():
            key = dotenv_values(env).get("ROBOFLOW_API_KEY")
            if key:
                return key
    return os.environ.get("ROBOFLOW_API_KEY")


def image_b64(value):
    """Annotated image as either {"type":"base64","value":...} or a bare base64 string."""
    if isinstance(value, dict):
        return value.get("value")
    return value if isinstance(value, str) else None


def strip_images(obj):
    if isinstance(obj, dict):
        if obj.get("type") == "base64" and "value" in obj:
            return {"type": "base64", "value": "<stripped>"}
        return {k: "<stripped base64 jpeg>" if k == "annotated_image" and isinstance(v, str)
                else strip_images(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [strip_images(v) for v in obj]
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--inline", action="store_true")
    ap.add_argument("--out", default=tempfile.gettempdir())
    ap.add_argument("--raw")
    ap.add_argument("--api-url", default="https://serverless.roboflow.com")
    ap.add_argument("--menu")
    args = ap.parse_args()

    client = InferenceHTTPClient(api_url=args.api_url, api_key=find_key())
    params = {"menu": [m.strip() for m in args.menu.split(",")]} if args.menu else {}
    kw = ({"specification": json.loads((HERE / "intake-plate.json").read_text(encoding="utf-8"))}
          if args.inline else {"workspace_name": WORKSPACE, "workflow_id": WORKFLOW_ID})

    for img in args.images:
        t0 = time.time()
        for attempt in range(3):
            # Serverless sometimes 404s on the saved-Workflow fetch for a few seconds; retry.
            try:
                res = client.run_workflow(images={"image": img}, parameters=params, **kw)[0]
                break
            except HTTPCallErrorError as e:
                if attempt == 2 or e.status_code != 404:
                    raise
                time.sleep(3)
        dt = time.time() - t0
        stem = Path(img).stem
        print(json.dumps({"image": img, "seconds": round(dt, 2), "qr": res.get("qr"),
                          "estimate": res.get("estimate")}, indent=2))
        b64 = image_b64(res.get("annotated_image"))
        if b64:
            out = Path(args.out) / f"{stem}_annotated.jpg"
            out.write_bytes(base64.b64decode(b64))
            print(f"annotated -> {out}")
        if args.raw:
            Path(args.raw).mkdir(parents=True, exist_ok=True)
            (Path(args.raw) / f"{stem}.json").write_text(
                json.dumps(strip_images(res), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
