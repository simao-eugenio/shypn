#!/bin/bash
# Run detailed experiments on representative models

MODELS=(
  "BIOMD0000000001:../../doc/papers/foundation/experimental_data/biomodels_dataset/sbml_files/BIOMD0000000001.xml:small"
  "BIOMD0000000007:../../doc/papers/foundation/experimental_data/biomodels_dataset/sbml_files/BIOMD0000000007.xml:medium"
  "BIOMD0000000019:../../doc/papers/foundation/experimental_data/biomodels_dataset/sbml_files/BIOMD0000000019.xml:large"
)

OUTPUT="../../workspace/sample_experiments"
mkdir -p "$OUTPUT"

for model_spec in "${MODELS[@]}"; do
    IFS=':' read -r model_id model_path size <<< "$model_spec"
    echo ""
    echo "========================================"
    echo "Processing $model_id ($size model)"
    echo "========================================"
    
    model_output="$OUTPUT/$model_id"
    mkdir -p "$model_output"
    
    echo "1. Validation (20 replicates)..."
    timeout 300 python3 validate_equivalence.py "$model_path" -n 20 -d 100.0 -o "$model_output" 2>&1 | \
        grep -v "Converted React" | grep -v "CONVERTER INPUT" | grep -v "Enabling stochastic" | tail -8
    
    echo ""
    echo "2. Benchmark (20 replicates)..."
    timeout 300 python3 benchmark_timing.py "$model_path" -n 20 -d 100.0 --compare -o "$model_output" 2>&1 | \
        grep -v "Converted React" | grep -v "CONVERTER INPUT" | grep -v "Enabling stochastic" | tail -8
    
    echo ""
done

echo ""
echo "========================================"
echo "Summary"
echo "========================================"
echo "Results saved to: $OUTPUT"
ls -lh "$OUTPUT"/*/validation_results.json "$OUTPUT"/*/benchmark_results.json 2>/dev/null | awk '{print $9, $5}'
