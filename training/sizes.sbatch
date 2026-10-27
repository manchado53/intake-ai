#!/bin/bash
#SBATCH --job-name=intake_size
#SBATCH --partition=dgxh100
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --array=0-3
#SBATCH --output=%x_%A_%a.log
# v1b recipe at four more model sizes (Small = runs/v1b already). One GPU per size, in parallel.
SIZES=(Nano Medium Large XLarge)
cd ~/intake-train || exit 1
source .venv/bin/activate
export SIZE=${SIZES[$SLURM_ARRAY_TASK_ID]}
nvidia-smi --query-gpu=name,memory.used --format=csv,noheader
python -u train_variant.py export_v2 v1b "${EPOCHS:-50}"
