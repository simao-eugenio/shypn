#!/bin/bash
# Activate the conda environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate shypn

# Set environment variables
export LIBGL_ALWAYS_SOFTWARE=1
export GDK_BACKEND=x11

# Run the main Python launcher and suppress non-critical messages
python3 src/shypn.py > /dev/null 2>&1
