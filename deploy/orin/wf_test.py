"""Time 3 Workflow runs on the local Inference server.  Run on the Orin from ~/intake: venv/bin/python wf_test.py [image]"""
import json, sys, time, cv2
from dotenv import dotenv_values
from inference_sdk import InferenceHTTPClient
cfg = dotenv_values(".env")
c = InferenceHTTPClient(api_url="http://localhost:9001", api_key=cfg["ROBOFLOW_API_KEY"])
spec = json.load(open("workflow/intake-plate.json"))
menu = ["white fish", "pasta", "carrots"]  # one resident's plate (<= 8 words)
img = cv2.imread(sys.argv[1] if len(sys.argv) > 1 else "data/raw/test_station/01_R01_s0.png")
for k in range(3):
    t = time.time()
    try:
        out = c.run_workflow(workspace_name="manchado53", specification=spec, images={"image": img}, parameters={"menu": menu})
    except Exception as ex:
        print("ERR", str(ex)[:1500]); break
    e = out[0]["estimate"]
    print("run %d: %.1fs plate=%s total=%s" % (k, time.time() - t, e["plate_found"], e["food_frac_total"]),
          [(i["name"], i["area_frac"]) for i in e["items"]], flush=True)
