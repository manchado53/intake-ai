# Candidate brief — summary

Source: `FE Tech Challenge - Candidate Brief.pdf` (this folder). Replicates a Roboflow
proof event (basic PoC) from a commercial engagement, first mile to last mile.

## Requirements → how Intake.ai meets them

| Brief says | Required? | Intake.ai |
|---|---|---|
| Use case centered on a business problem | yes | Nursing homes chart meal intake by eye (~15–20 pt overestimate); undernutrition is caught late |
| **Own data** (local camera, RTSP…) uploaded to Roboflow | **must** | Orbbec color+depth photos of staged meals |
| Universe / other datasets to augment | optional | maybe, only if v1 masks are weak |
| Label with platform features | yes | SAM 3 auto-label + manual fixes |
| **Model training**: pick project type, model size, augmentations "to solve your problem in production" | yes | Instance segmentation, small model (RF-DETR seg) for the Orin |
| Workflow using your model(s) | yes | QR + food seg + custom block + Slack |
| **Custom Workflow Block** | **must** | Intake estimator: masks + depth → % eaten → protein/kcal |
| Deploy with **Roboflow Inference** | yes | Inference on Jetson Orin Nano, offline |
| Actionable insights (PLC, reports, HMI, alerts) | yes | Station screen, daily/weekly report, Slack alert (<50% ×3 meals) |

## Demo format
- Vendor-to-prospect style; slides allowed.
- **30 minutes, hard stop. Demo must be live, not recorded.**
- 15–30 min debrief after.

## Assessed on
Technical expertise · Communication · Presentation · Problem-solving.
