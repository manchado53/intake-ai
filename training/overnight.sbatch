#!/bin/bash
#SBATCH --job-name=intake_v
#SBATCH --partition=dgxh100
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --output=%x_%j.log
# Overnight: v0 (our meals), v1 (+ public), v1b (+ colour aug). Same valid/test for all.
cd ~/intake-train || exit 1
source .venv/bin/activate
nvidia-smi --query-gpu=name --format=csv,noheader
for v in v0 v1 v1b; do
  echo "=== $v $(date)"
  python -u train_variant.py export_v2 "$v" "${EPOCHS:-50}" || echo "FAILED $v"
done
echo "=== done $(date)"
