#!/bin/bash
# Test script to check viability panel initialization

cd /home/simao/projetos/shypn
python3 -u src/shypn.py 2>&1 | tee /tmp/shypn_test.log
