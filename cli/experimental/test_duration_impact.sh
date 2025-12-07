#!/bin/bash
# Test how simulation duration affects τ-leaping speedup

MODEL="../../doc/papers/foundation/experimental_data/biomodels_dataset/sbml_files/BIOMD0000000007.xml"
OUTPUT="../../workspace/duration_test"
mkdir -p "$OUTPUT"

echo "Testing τ-leaping speedup vs simulation duration"
echo "Model: BIOMD0000000007 (22 species, 25 reactions)"
echo ""

DURATIONS=(50 100 200 500 1000 2000)

for duration in "${DURATIONS[@]}"; do
    echo "Duration: $duration time units"
    timeout 300 python3 benchmark_timing.py "$MODEL" -n 20 -d "$duration" --compare -o "$OUTPUT/d${duration}" 2>&1 | \
        grep -E "Speedup|Time:" | tail -3
    echo ""
done

echo "Summary:"
echo "Duration | τ-leaping | Gillespie | Speedup"
echo "---------|-----------|-----------|--------"
for duration in "${DURATIONS[@]}"; do
    if [ -f "$OUTPUT/d${duration}/benchmark_results.json" ]; then
        python3 -c "
import json
with open('$OUTPUT/d${duration}/benchmark_results.json', 'r') as f:
    data = json.load(f)
tau_time = data.get('tau_leaping', {}).get('total_time', 0)
gill_time = data.get('gillespie', {}).get('total_time', 0)
speedup = data.get('speedup', 0)
print(f'  {$duration:>5d}  | {tau_time:>8.3f}s | {gill_time:>8.3f}s | {speedup:>6.2f}x')
"
    fi
done
