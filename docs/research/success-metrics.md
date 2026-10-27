# Success metrics for the Intake.ai PoC

Researched 2026-10-27. Question: which metrics should a small instance-segmentation PoC report? Focus on what Roboflow recommends, plus the % eaten business metric.

**Short answer:** report three layers.

```
model metric (mask mAP, recall)   ->  "does it see food + plate?"
task metric  (% eaten vs scale)   ->  "is the number right?"      <- the one that sells
ops metric   (latency, flags)     ->  "can a kitchen run it?"
```

Roboflow's own docs give a reason to lead with the task metric. In their bolt-counting Workflow Evals tutorial, SAM3 masks scored **0.91 mIoU yet passed 0 of 5 count checks** ([docs](https://docs.roboflow.com/workflows/tutorials/compare-models-with-workflow-evals.md)). A high mask score did not mean the task was right.

---

## 1. Model metrics Roboflow reports (instance seg)

| Metric | What Roboflow shows | Source |
|---|---|---|
| mAP@50, mAP@50:95, mAP@75 | `map50_95` averages IoU 0.50 to 0.95 "in steps of 0.05 (the COCO standard)" | [Evaluate Trained Models](https://docs.roboflow.com/models/evaluate/evaluate-trained-models) |
| Boundary AP (mBAP@50/50:95/75) | Instance seg only. Boundary IoU "compares narrow bands along each mask edge, so it shows edge errors that mask IoU can hide" | same page; [Compare Trained Models](https://docs.roboflow.com/models/evaluate/compare-trained-models.md) |
| Precision / Recall / F1 vs confidence | "Production metrics explorer". Picks an **optimal confidence** and applies it as the default for inference | [Evaluate Trained Models](https://docs.roboflow.com/models/evaluate/evaluate-trained-models) |
| Confidence sweep API | `optimalThreshold` = threshold that maximizes F1, per split and class | [confidence-sweep](https://docs.roboflow.com/developer/rest-api/model-evaluations/confidence-sweep) |
| Confusion matrix | Correct, FP, FN. Click a cell to see the images | [Evaluate Trained Models](https://docs.roboflow.com/models/evaluate/evaluate-trained-models) |
| Performance by class | Per-class correct / misclassified / FN / FP at a chosen threshold | same |
| Vector explorer | Image clusters with F1/P/R each. Finds where the model is weak | same |
| Median latency | Serverless test-set median, no network time | same |
| Model comparison | Default frontier metric for instance seg = **mAP@50:95**. Pareto plot of accuracy vs latency | [Compare Trained Models](https://docs.roboflow.com/models/evaluate/compare-trained-models.md) |
| Instance-seg evaluation | Added Oct 2025: mAP by object size, ideal threshold, per-class accuracy | [changelog](https://docs.roboflow.com/changelog/explore-by-month/october-2025/model-evaluation-for-instance-segmentation-models) |

**How Roboflow says to read them**
- mAP is a 0-1 summary. "A high mAP means that a model has both a low false negative and a low false positive rate." Use it to **compare models** ([blog](https://roboflow.com/blog/mean-average-precision)).
- Use **mAP@50:95** when exact localization matters. mAP@50 "does not provide a complete picture of localization quality" ([blog](https://roboflow.com/blog/map-0-5-vs-map-0-5-0-95)). Our % eaten comes from mask **area**, so 50:95 (and boundary AP) fit better than mAP@50.
- mAP "does not tell you which confidence threshold to use in production". The threshold "is an error-cost decision". Keep a fixed golden set and "reuse the same images when evaluating future model versions" ([blog](https://roboflow.com/blog/how-to-set-a-confidence-threshold-for-object-detection)).
- **What is "good"?** Roboflow gives **no numeric target** for mAP, P, R or F1. Checked: the evaluate docs, the mAP blog and the mAP50-vs-50:95 blog. Its guidance is to compare against a baseline on your own test set.
- Mask vs box: the [supervision `MeanAveragePrecision`](https://supervision.roboflow.com/latest/metrics/mean_average_precision/) scores masks with `MetricTarget.MASKS`. It reports map50/75/50_95, small/medium/large and per-class AP. For a seg PoC, report **mask (segm)** mAP, not box mAP.

**Context for our 0.88**
- RF-DETR-Seg-S on COCO scores AP50:95 **43.1**, AP50 66.2, 4.4 ms at 384x384 ([rfdetr docs](https://rfdetr.roboflow.com/latest/)). The docs do not say whether this is mask or box AP, and the hardware for the seg table is not stated (**unverified**).
- COCO has 80 classes and many small objects. We have 2 classes and large objects. **Do not compare 0.88 with 43.1.** Compare against our own baseline instead.

## 2. Roboflow guidance that ties metrics to the business

| Tool | What it measures | Use for us | Source |
|---|---|---|---|
| **Workflow Evals** | Checks any Workflow output against ground truth: exact match, "Custom rule" with a tolerance, "Latency budget" per Case. Plots quality vs latency | Put `pct_eaten` in a Workflow output. Check `abs(err) <= 10 pp` and add a latency budget | [Workflow Evals](https://docs.roboflow.com/workflows/evaluate/workflow-evals.md) |
| Eval tutorial | "This is where you define success." Ranks candidates by **average error, then bias, then exact matches, then latency** | Use the same order: MAE, bias, bin agreement, latency | [tutorial](https://docs.roboflow.com/workflows/tutorials/compare-models-with-workflow-evals.md) |
| Active Learning | Samples production images by rules, for example "confidence falls below 60%", class, or detection count, then queues them for review | Collect low-confidence plates and odd blob counts | [Active Learning](https://docs.roboflow.com/deployment/monitoring-and-analytics/active-learning.md) |
| Model Monitoring | Total requests, **average confidence**, average inference time, class distribution. Being replaced by Vision Events | Watch for confidence drift after a menu change | [Model Monitoring](https://docs.roboflow.com/deployment/monitoring-and-analytics/model-monitoring.md) |
| Vision Events: Operator Feedback | Operators mark events correct / incorrect / inconclusive | A staff "looks wrong" tap gives a live accuracy proxy | [llms.txt index](https://docs.roboflow.com/llms.txt) (page title only, **not read in full**) |
| Edge benchmarking | `inference benchmark` reports throughput, latency and errors on your device | Measure on the Orin | [Benchmark Inference](https://docs.roboflow.com/reference/inference/inference-cli/benchmark.md) |

RF-DETR edge post: report **end-to-end** latency, measured like-for-like (TensorRT FP16, batch 1), and pair speed with accuracy on your own data ([blog](https://roboflow.com/blog/rf-detr-for-the-edge)).

## 3. Business metric: % eaten. What the literature uses

**Error metrics in use**

| Metric | Example | Source |
|---|---|---|
| Mean percent intake error (bias) and absolute intake error | Pfisterer et al. 2022 (LTC plates, RGB-D): mean % intake error **-4.2%**. Calls **<10% error an acceptable margin**, vs "current practice is up to 62% error" | [arXiv 1910.11250](https://arxiv.org/abs/1910.11250) / Sci Rep [10.1038/s41598-021-03972-8](https://doi.org/10.1038/s41598-021-03972-8) |
| IoU + 2D vs 3D % intake error | 2D-only (area) intake error was **-23.4% +/- 21.2** (EDFN, regular texture). Depth-refined 3D error was **-0.8% +/- 5.2**. "Standard segmentation metrics are insufficient due to visual-volume discordance" | same |
| Correlation + Bland-Altman | Digital photography vs weighing: r = 0.92 (Williamson 2003; **secondary source only**). A 2025 hospital abstract reports rs = 0.99 and good Bland-Altman agreement | [summary search hit](https://pmc.ncbi.nlm.nih.gov/articles/PMC4138603/) (**unverified**); [NSA 2025 abstract](https://nsa-2025.m.asnevents.com.au/schedule/session/27190/abstract/129505) |
| Mean diff +/- SD vs weighed | Hospital food charts overestimated by 3.2 +/- 14.7%. Photography overestimated by 4.7 +/- 15.8% | [WUR thesis](https://edepot.wur.nl/686706) (seen via search snippet, **not read in full**) |

**Staff baseline (what we beat)**

| Finding | Number | Source |
|---|---|---|
| Staff documentation vs research observation/photo, 56 NH residents | Staff 79.3% vs observed 58.9% and photo 58.2%: about **20 pts over**. Staff missed **19 of 36** at-risk residents | Simmons & Reuben, JAGS 2000;48:209-13, via [AAFP summary](https://www.aafp.org/afp/2000/0801/p637a) |
| LTC staff estimates correct | **44%** routine, **38%** with delayed recording | Castellanos & Andrews, JADA 2002;102:826-30, as cited in [Pfisterer](https://arxiv.org/abs/1910.11250) (primary **not read**) |
| Charting is coarse | Recorded in **25% bins** | [Pfisterer](https://arxiv.org/abs/1910.11250) |
| Trained CNAs, simulated items | 85% of 384 estimates correct, kappa 0.80 | [FIU thesis](https://digitalcommons.fiu.edu/etd/1289) (abstract only) |

**Takeaway**
- Staff in the 0/25/50/75/100 system are right about **4 times in 10** and lean **high**. They miss low eaters, and low eaters are the residents who matter.
- A tool that is within +/-10 pp and unbiased is a clear upgrade.
- **Caveat for us:** we use top-down **area**. Pfisterer shows area alone can under-read intake by about 20%, for example a thin sauce smear that looks big. Our kitchen-scale grams check whether **area % tracks mass %**. Report that check honestly.

## 4. Recommended metric stack for the demo

Targets marked *ours* are judgement calls, not taken from a source.

| Layer | Metric | Target | Why |
|---|---|---|---|
| **Model** | Mask mAP@50:95 on unseen meal (not box) | >= 0.80; now about 0.88 | Roboflow's default instance-seg comparison metric ([docs](https://docs.roboflow.com/models/evaluate/compare-trained-models.md)). Area needs tight masks |
| Model | Boundary AP (mBAP@50:95), if eval shows it | Report it; no target | Edge errors move area, and mask IoU can hide them ([docs](https://docs.roboflow.com/models/evaluate/evaluate-trained-models)) |
| Model | Plate recall at deployment confidence | 100% on test (*ours*) | No plate means no normalization and no number |
| Model | Food P/R/F1 at **F1-optimal confidence** from the sweep | Report it, then confirm on % eaten | Roboflow picks the threshold this way ([sweep](https://docs.roboflow.com/developer/rest-api/model-evaluations/confidence-sweep)) |
| Model | Blob count exact % | Keep as a diagnostic only | Same idea as the Roboflow exact-count check ([tutorial](https://docs.roboflow.com/workflows/tutorials/compare-models-with-workflow-evals.md)), but count does not drive % eaten |
| **Task** (headline) | **MAE of % eaten vs scale**, in percentage points | **<= 10 pp** | Pfisterer's "acceptable error margin of less than 10%" ([arXiv](https://arxiv.org/abs/1910.11250)) |
| Task | Bias (mean signed error) | Within +/-5 pp (*ours*) | Staff bias is about +20 pts ([AAFP](https://www.aafp.org/afp/2000/0801/p637a)) |
| Task | Bland-Altman 95% limits of agreement | Report them; aim inside +/-20 pp (*ours*) | Standard agreement plot in diet validation ([NSA 2025](https://nsa-2025.m.asnevents.com.au/schedule/session/27190/abstract/129505); Bland & Altman, Lancet 1986, **not fetched**) |
| Task | 25%-bin agreement (same bin as the scale) | >= 80% (*ours*) vs staff 44% | Speaks the charting language staff already use ([Pfisterer](https://arxiv.org/abs/1910.11250)) |
| Task | Low-eater catch rate (scale < 50% eaten -> flagged) | >= 90% recall (*ours*) | Staff missed 53% of at-risk residents ([AAFP](https://www.aafp.org/afp/2000/0801/p637a)) |
| **Ops** | End-to-end latency per plate on Jetson Orin (TRT FP16, bs 1) | < 1 s for photo to % (*ours*). Model alone is expected to be tens of ms | Roboflow has **no published Orin seg number**. Orin NX rfdetr-small **detection** runs 52.5 inf/s TRT. Seg-small on L4 runs 126.7 inf/s TRT ([benchmarks](https://docs.roboflow.com/reference/inference/inference-python/benchmarks.md)). Measure with `inference benchmark` |
| Ops | Workflow Evals latency budget pass rate | 100% of Cases | [Workflow Evals](https://docs.roboflow.com/workflows/evaluate/workflow-evals.md) |
| Ops | Review flag rate: low confidence or plate missing, sent to Active Learning | <= 10% of trays (*ours*) | [Active Learning](https://docs.roboflow.com/deployment/monitoring-and-analytics/active-learning.md) |
| Ops | Average confidence drift week over week | Alert on a sharp drop (*ours*) | [Model Monitoring](https://docs.roboflow.com/deployment/monitoring-and-analytics/model-monitoring.md) |
| Ops | Staff seconds per tray, vs eyeballing and charting | Lower than today (*ours*, not measured) | Visual estimation already takes about half the time of weighing (NH study, search snippet, **unverified**) |

**One-line pitch:** "Mask mAP 0.88 says the model sees the food. MAE vs the kitchen scale says the number is right. Staff are right 44% of the time and read 20 points high."

## Unverified / gaps
- Whether the RF-DETR seg table reports mask or box AP, and its hardware.
- RF-DETR-Seg latency on Jetson Orin: no Roboflow figure found.
- Castellanos & Andrews 2002 and Williamson 2003: primary texts not read (cited through Pfisterer and a review).
- No Roboflow source gives a numeric "good mAP" threshold.
- Bland & Altman 1986: standard reference, not fetched.
