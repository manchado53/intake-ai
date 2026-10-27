#!/bin/bash
#SBATCH --job-name=intake_eval
#SBATCH --partition=dgxh100
#SBATCH --gres=gpu:h100:1
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=%x_%j.log
cd ~/intake-train && source .venv/bin/activate && python -u eval_pub.py
