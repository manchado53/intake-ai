# Orin setup: Roboflow Workflow on Inference (Jetson Orin Nano Super 8GB)

Goal: run our Workflow (RF-DETR Seg Small + Custom Python + Visualization, maybe Dataset Upload)
on Roboflow Inference on the Orin, for the live demo **Wed 2026-10-28, 12 pm CDT**.
Research only (checked 2026-10-27). Nothing here has been run on the device yet.
**Unverified** = I could not confirm it from a primary source; test it on the device.

## Answers first

| Question | Answer | Source |
|---|---|---|
| Image | JetPack 6.2.x (L4T R36.4.3+) -> `roboflow/roboflow-inference-server-jetson-6.2.0`. Pin a version: `1.8.3` (= `latest`, pushed 2026-10-26) or `1.8.2` (2026-10-23). ~3.3 GB download, ~8.1 GB on disk. | [Jetson install](https://docs.roboflow.com/deployment/self-hosted/inference-server/install/jetson), [Docker Hub tags](https://hub.docker.com/r/roboflow/roboflow-inference-server-jetson-6.2.0/tags) |
| JetPack 6.0 (L4T R36.3)? | `jetson-6.0.0` image is **frozen at 1.3.1** (June 2026), no longer built. JetPack 5 (R35) -> `jetson-5.1.1` (14.9 GB download). | [Docker Hub 6.0.0](https://hub.docker.com/r/roboflow/roboflow-inference-server-jetson-6.0.0/tags), [security migration](https://docs.roboflow.com/deployment/self-hosted/inference-server/configuration/security-migration) |
| Custom Python on self-hosted? | **Yes, on by default.** `ALLOW_CUSTOM_PYTHON_EXECUTION_IN_WORKFLOWS=True`, `WORKFLOWS_CUSTOM_PYTHON_EXECUTION_MODE=local`. No env var needed. | [Env vars](https://docs.roboflow.com/deployment/self-hosted/inference-server/configuration/environment-variables), [`env.py`](https://github.com/roboflow/inference/blob/main/inference/core/env.py) |
| Custom Python on hosted? | **Yes**, on Serverless Cloud API (`https://serverless.roboflow.com`, sandboxed containers) and Dedicated Deployments. The legacy v1 hosted API does not. So we can test the Workflow **today** from the laptop with no Orin. | [Custom blocks](https://docs.roboflow.com/workflows/blocks/blocks/custom-blocks), [changelog Aug 2025](https://docs.roboflow.com/changelog/explore-by-month/august-2025/run-custom-python-on-workflows), [forum: v1 error](https://discuss.roboflow.com/t/change-environmental-variable-allow-custom-python-execution-in-workflows-true-error/10808) |
| RF-DETR Seg on Inference? | Yes. `rfdetr-seg-*` runs on self-hosted Inference; custom weights uploaded with `-t rfdetr-seg-small` are supported. Jetson images run the `inference-models` backend (`USE_INFERENCE_MODELS=True`). Our model exists: `rfdetr-seg-small`, instance-seg, training "finished". **Unverified:** RF-DETR **Seg** speed on an Orin Nano (Roboflow only publishes Orin NX **detection** numbers), and whether a TRT engine is used for a custom upload or it falls back to Torch/ONNX. | [RF-DETR docs](https://docs.roboflow.com/models/supported-models/rf-detr), [benchmarks](https://docs.roboflow.com/reference/inference/inference-python/benchmarks), [Jetson 6.2 Dockerfile](https://github.com/roboflow/inference/blob/main/docker/dockerfiles/Dockerfile.onnx.jetson.6.2.0) |
| Offline? | Mostly yes, after one online warm-up: weights live in the mounted cache; the Workflow spec has a **file cache** used on connection errors. Safest: send the spec **inline** (no API fetch at all). Dataset Upload needs internet. | See step 9 |

## Checklist (total ~2-2.5 h if it goes well; budget 3.5 h)

Run as the robot's normal user, in our own folder (`~/intake`). Don't edit ROS files, systemd units, or `/etc`.

### 1. Check the device (5 min)
```bash
cat /etc/nv_tegra_release               # "R36 (release), REVISION: 4.3" = JetPack 6.2
dpkg-query --show nvidia-jetpack        # may be missing on custom robot images
sudo nvpmodel -q                        # current power mode
free -h; df -h / ; docker --version; docker info | grep -i runtime
docker ps                               # what robot containers already run
systemctl list-units --type=service --state=running | grep -i -E "ros|robot|start|hiwonder"
```
L4T -> JetPack: R36.3 = 6.0, R36.4 = 6.1, R36.4.3 = 6.2, R36.4.4 = 6.2.1, R36.5.x = 6.2.2/6.2.3
([NVIDIA JetPack archive](https://developer.nvidia.com/embedded/jetpack-archive)).
The Inference CLI does the same check: it reads `/etc/nv_tegra_release`, falls back to `dpkg nvidia-jetpack`,
and maps R36.4+ to the 6.2.0 image, R36.0-36.3 to 6.0.0, R35 to 5.1.1
([`container_adapter.py`](https://github.com/roboflow/inference/blob/main/inference_cli/lib/container_adapter.py)).
Need >= 10 GB free disk (Roboflow says 10 GB; I'd want 15 GB with the cache).

**Stop here if:** no `nvidia` runtime in `docker info`, or L4T is R36.3 / R35. See risks table.

### 2. Max performance (2 min, may need a reboot)
```bash
sudo nvpmodel -m 2      # MAXN_SUPER on Orin Nano 8GB Super (0 = 15W, 1 = 25W default)
sudo jetson_clocks      # pin clocks to max until next reboot
```
Mode IDs per [NVIDIA power guide (r36.4.3)](https://docs.nvidia.com/jetson/archives/r36.4.3/DeveloperGuide/SD/PlatformPowerAndPerformance/JetsonOrinNanoSeriesJetsonOrinNxSeriesAndJetsonAgxOrinSeries.html).
MAXN_SUPER exists only if the board was flashed with the `jetson-orin-nano-devkit-super` config. Changing mode can ask
for a reboot. The mode **persists** across reboots, so note the old mode (`nvpmodel -q`) and set it back after the demo.
`jetson_clocks` resets at reboot. The robot runs on a 19 V bench cable, so power is fine; watch heat.

### 3. Free memory, temporarily (5 min)
The Orin Nano shares 8 GB between CPU and GPU. Only temporary moves (all undone by a reboot):
```bash
docker stop <robot-container>            # if the robot stack runs in Docker; start it again after
sudo systemctl stop <robot-service>      # stop, NOT disable; unit files untouched
sudo init 3                              # drop the desktop, ~800 MB back (sudo init 5 to restore)
sudo fallocate -l 8G ~/intake/8GB.swap && sudo chmod 600 ~/intake/8GB.swap \
  && sudo mkswap ~/intake/8GB.swap && sudo swapon ~/intake/8GB.swap   # no fstab edit = gone at reboot
```
Desktop and swap tips from [jetson-containers setup](https://github.com/dusty-nv/jetson-containers/blob/master/docs/setup.md)
(it also disables zram and edits fstab; skip those, they are permanent).
Watch memory with the built-in `tegrastats` (no install). `jtop` needs `sudo pip3 install jetson-stats`, which adds a
system service; skip it on the borrowed robot ([jetson-stats](https://github.com/rbonghi/jetson_stats)).

### 4. Pull the image (10-20 min on good Wi-Fi; do it first, in the background)
```bash
docker pull roboflow/roboflow-inference-server-jetson-6.2.0:1.8.3
```
Pin the tag so a new `latest` can't change things the night before.
Optional: also `docker save` it to a tar on the NVMe as a no-internet backup.

### 5. Start the server (2 min)
Roboflow's documented command, with a pinned tag and our cache folder:
```bash
mkdir -p ~/intake/inference-cache
sudo docker run -d \
    --name inference-server \
    --runtime nvidia \
    --read-only \
    -p 9001:9001 \
    --volume ~/intake/inference-cache:/tmp:rw \
    --security-opt="no-new-privileges" \
    --cap-drop="ALL" \
    --cap-add="NET_BIND_SERVICE" \
    roboflow/roboflow-inference-server-jetson-6.2.0:1.8.3
docker logs -f inference-server          # wait for uvicorn "running on 0.0.0.0:9001"
curl http://localhost:9001/info
```
From [Jetson install](https://docs.roboflow.com/deployment/self-hosted/inference-server/install/jetson).
`/tmp` in the container holds the model cache (`MODEL_CACHE_DIR=/tmp/cache`), ORT engines (`/tmp/ort_cache`) and Triton
cache (`/tmp/triton-cache`), so this one mount keeps everything across restarts
([Dockerfile ENV block](https://github.com/roboflow/inference/blob/main/docker/dockerfiles/Dockerfile.onnx.jetson.6.2.0),
[Docker config](https://docs.roboflow.com/deployment/self-hosted/inference-server/configuration/docker-configuration)).

- **Port:** `-p 9001:9001` opens it to the whole network, with no auth, and Custom Python = remote code execution.
  OK on a private hotspot for the demo. If the client runs on the Orin itself, use `-p 127.0.0.1:9001:9001`
  ([security](https://docs.roboflow.com/deployment/self-hosted/inference-server/configuration/security)).
- **API key:** don't put it in the container. The client sends it per request (step 7).
- **TensorRT via ONNX Runtime (optional):** add
  `-e ONNXRUNTIME_EXECUTION_PROVIDERS="[TensorrtExecutionProvider,CUDAExecutionProvider,CPUExecutionProvider]"`.
  First load "sometimes 15+ minutes" per model; the engine is cached in the mount. The image already sets
  `ORT_TENSORRT_FP16_ENABLE=1`, `ORT_TENSORRT_ENGINE_CACHE_ENABLE=1`, `ORT_TENSORRT_MAX_WORKSPACE_SIZE=4294967296` (4 GB).
  On 8 GB, consider `-e ORT_TENSORRT_MAX_WORKSPACE_SIZE=1073741824` (**unverified** that it's needed or used by the
  `inference-models` path). Try without TRT first; add it only if latency misses the < 1 s target.

**CLI path (alternative):** `pip install inference-cli && inference server start`. It auto-detects Jetson, picks the
image by L4T, runs it `--privileged` with `runtime=nvidia`, publishes on `0.0.0.0:9001`, caps it at `mem_limit=4g`,
`memswap_limit=6g`, and mounts **host `/tmp`** as the cache. Host `/tmp` is wiped on reboot, so the cache and TRT engines
are lost. It also pulls `:latest` (no pinning). Use the manual `docker run` above for the demo
([`container_adapter.py`](https://github.com/roboflow/inference/blob/main/inference_cli/lib/container_adapter.py)).

### 6. Workflow ready + tested on hosted first (20 min, from the laptop, today)
- Build the Workflow in the app: model block -> Custom Python (area -> % eaten) -> Visualization (-> Dataset Upload).
- Custom Python gets `np`, `cv2`, `sv` (supervision), `math`, `json`, `shapely`... preloaded; no pip installs
  ([dynamic Python blocks](https://docs.roboflow.com/workflows/developer-guide/developer-guide/dynamic-python-blocks)).
- Run it against `https://serverless.roboflow.com` with the same client code (step 7). If it works there, the only new
  variable on the Orin is the hardware.
- Export the Workflow JSON into the repo (e.g. `workflows/intake.json`) for inline use (step 9).
- Model id: copy it from the model block in the Workflow editor. The platform shows
  `manchado53/intake-ai-food-seg-2-rfdetr-seg-small-t1`; the legacy form is `intake-ai-food-seg/2`.
  **Unverified** which form Inference 1.8.3 resolves for a custom upload; the editor's value is the safe one.

### 7. Call it (5 min)
```python
import os, cv2
from dotenv import load_dotenv
from inference_sdk import InferenceHTTPClient

load_dotenv()                                   # ROBOFLOW_API_KEY from the gitignored .env
client = InferenceHTTPClient(api_url="http://<orin-ip>:9001",   # or https://serverless.roboflow.com
                             api_key=os.environ["ROBOFLOW_API_KEY"])
frame = cv2.imread("plate.jpg")                 # numpy BGR frame works; so do PIL, base64, paths
result = client.run_workflow(
    workspace_name="manchado53", workflow_id="<workflow-id>",   # fetched from Roboflow API...
    # specification=json.load(open("workflows/intake.json")),  # ...or inline, no API fetch
    images={"image": frame},
    parameters={},
    # disable_sinks=True,                       # skip Dataset Upload / webhooks (e.g. when offline)
)
```
Signature: `run_workflow(workspace_name, workflow_id, specification, images, parameters, excluded_fields, use_cache,
enable_profiling, workflow_version_id, disable_sinks)`. "Supported images are numpy arrays, PIL.Image and base64
images, links to images and local paths" ([`inference_sdk/http/client.py`](https://github.com/roboflow/inference/blob/main/inference_sdk/http/client.py)).
Install on the client: `pip install inference-sdk python-dotenv`.

### 8. Warm up + benchmark (10 min; up to 30 min if TRT builds)
The first request downloads weights and loads the model (slow). Send 1-3 warm-up requests, then:
```bash
pip install inference-cli    # on laptop or Orin; reads ROBOFLOW_API_KEY from env
inference benchmark api-speed -h http://<orin-ip>:9001 \
  -wn manchado53 -wid <workflow-id> -d ./data/bench_plates -wr 5 -br 100 -o bench.json
# model only:  inference benchmark api-speed -h http://<orin-ip>:9001 -m <model-id> -d ./data/bench_plates
```
Options from [`inference_cli/benchmark.py`](https://github.com/roboflow/inference/blob/main/inference_cli/benchmark.py);
defaults `-wr 10`, `-br 1000`, dataset `coco`. Docs: [Benchmark Inference](https://docs.roboflow.com/reference/inference/inference-cli/benchmark).
Record p50/p95 latency in `docs/setup.md` (D9 ops target: photo -> % < 1 s).
Reference only: Orin NX `rfdetr-small` **detection** 13.9 inf/s ONNX, 52.5 TRT; no Orin Nano seg number exists
([benchmarks](https://docs.roboflow.com/reference/inference/inference-python/benchmarks)).

### 9. Offline drill (15 min)
1. Online: run the Workflow once (weights -> `~/intake/inference-cache`; spec -> file cache).
2. Disconnect Wi-Fi/Ethernet. Run again with **the inline spec** and `disable_sinks=True`. Then try the
   workflow-id form too.
3. Restart the container (`docker restart inference-server`) while offline and run again. This is the real test.

What the source says:
- Workflow spec: kept in memory 15 min (`WORKFLOWS_DEFINITION_CACHE_EXPIRY=900`). On `ConnectionError`/`Timeout`, the
  server falls back to a **file cache** (`USE_FILE_CACHE_FOR_WORKFLOWS_DEFINITIONS=True`, under `MODEL_CACHE_DIR`)
  ([`roboflow_api.py`](https://github.com/roboflow/inference/blob/main/inference/core/roboflow_api.py), [`env.py`](https://github.com/roboflow/inference/blob/main/inference/core/env.py)).
  The inline spec skips the fetch entirely.
- Weights: stored in `/tmp/cache` in the container; lost without a mounted volume
  ([Docker config](https://docs.roboflow.com/deployment/self-hosted/inference-server/configuration/docker-configuration)).
  Formal `OFFLINE_MODE` with a 30-day weight lease is documented as an **Enterprise** feature
  ([Offline Mode](https://docs.roboflow.com/deployment/self-hosted/enterprise/offline-mode)).
  **Unverified:** whether a non-Enterprise server reloads a cached custom model after a restart with no internet.
  Step 9.3 answers it. If it fails, keep the container running from the online warm-up through the demo.
- Dataset Upload (Active Learning) needs internet; offline it returns `error_status`/`message` per image instead of
  uploading ([block source](https://github.com/roboflow/inference/blob/main/workflows/roboflow_workflows/core_steps/sinks/roboflow/dataset_upload/v2.py)).
  For the demo, run it with internet on, or show it with the hosted run.

### 10. After the demo (5 min)
`docker stop inference-server`, `sudo swapoff ~/intake/8GB.swap && rm ~/intake/8GB.swap`, `sudo nvpmodel -m <old>`,
`sudo init 5`, restart any robot service/container you stopped (or just reboot).

## Time budget

| Step | Time |
|---|---|
| 1 Check device | 5 min |
| 2 Power mode | 2 min (+ reboot ~2 min) |
| 3 Free memory | 5 min |
| 4 Pull image | 10-20 min (parallel with 6) |
| 5 Start server | 2 min |
| 6 Hosted test + export spec (laptop) | 20 min |
| 7 Client call | 5 min |
| 8 Warm-up + benchmark | 10 min (30 with TRT) |
| 9 Offline drill | 15 min |
| Debug slack | 60 min |
| **Total** | **~2-2.5 h, plan 3.5 h** |

## Risks and pitfalls

| Risk | Sign | Fix | Source |
|---|---|---|---|
| Robot image is JetPack 6.0 (R36.3) or JetPack 5 (R35) | `nv_tegra_release` | 6.0: `jetson-6.0.0:1.3.1` (frozen June 2026; RF-DETR Seg on it **unverified**). 5: `jetson-5.1.1` (15 GB pull). Do **not** reflash the robot. Else fall back to the laptop. | [Docker Hub](https://hub.docker.com/r/roboflow/roboflow-inference-server-jetson-6.0.0/tags), [CLI map](https://github.com/roboflow/inference/blob/main/inference_cli/lib/container_adapter.py) |
| 6.2 image on an older 36.x host | container fails at start: "unsatisfied condition: cuda>=12.6" | image sets `NVIDIA_REQUIRE_CUDA="cuda>=12.6"` and is built on `l4t-jetpack:r36.4.0`. Use the image that matches L4T. (**Unverified** if a 6.0 host can force it.) | [Dockerfile](https://github.com/roboflow/inference/blob/main/docker/dockerfiles/Dockerfile.onnx.jetson.6.2.0) |
| Out of memory (8 GB shared CPU+GPU; ROS stack also running) | container killed, `tegrastats` RAM near full | step 3; one worker (`NUM_WORKERS=1` is the default); smaller TRT workspace; send frames at ~640 px, not 4K | [Env vars](https://docs.roboflow.com/deployment/self-hosted/inference-server/configuration/environment-variables) |
| TensorRT first-load build | first request hangs for minutes | build it the night before; cache is in the mount; or skip TRT | [Jetson install](https://docs.roboflow.com/deployment/self-hosted/inference-server/install/jetson) |
| No published RF-DETR **Seg** number on Orin Nano | unknown latency | measure in step 8; Roboflow recommends Orin NX 16 GB+ "for best performance" | [Jetson install](https://docs.roboflow.com/deployment/self-hosted/inference-server/install/jetson) |
| Cache lost on reboot (CLI path mounts host `/tmp`) | re-download / re-build after reboot | use the manual `docker run` with `~/intake/inference-cache` | [`container_adapter.py`](https://github.com/roboflow/inference/blob/main/inference_cli/lib/container_adapter.py) |
| `latest` changes overnight (1.8.3 shipped 2026-10-26) | behaviour differs from rehearsal | pin `:1.8.3`; `docker save` a backup | [Docker Hub](https://hub.docker.com/r/roboflow/roboflow-inference-server-jetson-6.2.0/tags) |
| Server open to the LAN with no auth + Custom Python | anyone on the network can run code | private hotspot; `-p 127.0.0.1:9001:9001` if the client is local; or `WORKSPACES_WHITELISTED_FOR_LOCAL_DEPLOYMENT=manchado53` (needs internet) | [Security](https://docs.roboflow.com/deployment/self-hosted/inference-server/configuration/security) |
| Offline restart can't reload the model (**unverified**) | 4xx/5xx after reboot with no internet | step 9.3 decides; keep the container up; venue Wi-Fi / phone hotspot | [Offline Mode](https://docs.roboflow.com/deployment/self-hosted/enterprise/offline-mode) |
| Docker on Jetson slower than bare metal for **video** pipelines | low FPS | we send single frames over HTTP, so this mostly doesn't apply | [issue #687](https://github.com/roboflow/inference/issues/687) |
| Disk full (image 8.1 GB + cache) | pull fails | check `df -h`; clean up with `docker image prune` (only our images) | [Jetson install](https://docs.roboflow.com/deployment/self-hosted/inference-server/install/jetson) |
| ARM wheels / onnxruntime-gpu / CUDA mismatch | import errors | don't `pip install inference` on the Orin host; the image ships its own ORT 1.x built with CUDA 12.6 + TensorRT 10.7 for sm87 | [Dockerfile](https://github.com/roboflow/inference/blob/main/docker/dockerfiles/Dockerfile.onnx.jetson.6.2.0) |
| Camera on the Orin: OpenNI depth stack is Windows-only in our setup | no frames | for v1 use the color stream (UVC) via OpenCV on the Orin, or keep the camera on the laptop and send frames to the Orin over HTTP | `docs/setup.md` |

## Fallback: same Workflow on the laptop

Same client code. Only `api_url` changes.

| Option | Command | Notes |
|---|---|---|
| A. Hosted (needs internet) | `api_url="https://serverless.roboflow.com"` | Custom Python works there. Zero setup. Best quick backup. |
| B. Docker Desktop, CPU | `pip install inference-cli && inference server start` (CPU image, binds `127.0.0.1:9001`), or `docker run -d --name inference-server --read-only -p 127.0.0.1:9001:9001 --volume "%USERPROFILE%\.inference\cache:/tmp:rw" --security-opt="no-new-privileges" --cap-drop="ALL" --cap-add="NET_BIND_SERVICE" roboflow/roboflow-inference-server-cpu:1.8.3` | Linux container -> `inference-models` backend on by default. CPU seg-small should be well under 1 s per photo (**unverified**, measure). Needs WSL 2. |
| C. Docker Desktop, NVIDIA GPU | same, with `--gpus all` and `roboflow/roboflow-inference-server-gpu` | Only if the laptop has an NVIDIA GPU + WSL 2 GPU support. |
| D. Native Windows installer | from [GitHub releases](https://github.com/roboflow/inference/releases) | `inference-models` is **off** on Windows by default; needs `$env:USE_INFERENCE_MODELS="True"` + admin or Developer Mode (symlinks). Least tested for RF-DETR Seg. |

Sources: [Windows install](https://docs.roboflow.com/deployment/self-hosted/inference-server/install/windows),
[Serverless Cloud API](https://docs.roboflow.com/deployment/roboflow-cloud/serverless-api),
[`env.py` Windows default](https://github.com/roboflow/inference/blob/main/inference/core/env.py).

Also record a backup video of the full Orin run (the prep call asked for one).
