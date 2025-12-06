#!/bin/bash
# Test the complete experimental validation workflow

set -e  # Exit on error

MODEL="../../doc/papers/foundation/experimental_data/biomodels_dataset/sbml_files/BIOMD0000000001.xml"
OUTPUT="../../workspace/workflow_test"
N_REPLICATES=10

echo "========================================="
echo "Testing Complete Experimental Workflow"
echo "========================================="
echo ""

# Clean output directory
rm -rf "$OUTPUT"
mkdir -p "$OUTPUT"

# 1. Validation
echo "1. Running validation (τ-leaping vs Gillespie)..."
python3 validate_equivalence.py "$MODEL" -n $N_REPLICATES -d 50.0 -o "$OUTPUT" 2>&1 | \
  grep -v "Converted React" | grep -v "CONVERTER INPUT" | tail -10
echo ""

# 2. Benchmark
echo "2. Running benchmark (timing comparison)..."
python3 benchmark_timing.py "$MODEL" -n $N_REPLICATES -d 50.0 --compare -o "$OUTPUT" 2>&1 | \
  grep -v "Converted React" | grep -v "CONVERTER INPUT" | tail -10
echo ""

# 3. Dependency Analysis
echo "3. Analyzing dependency structure..."
python3 analyze_dependency_impact.py "$MODEL" -n 5 -d 50.0 -o "$OUTPUT" 2>&1 | \
  grep -v "Converted React" | grep -v "CONVERTER INPUT" | tail -10
echo ""

# 4. Generate Report
echo "4. Generating comprehensive report..."
python3 generate_experiment_report.py \
  --validation "$OUTPUT/validation_results.json" \
  --benchmark "$OUTPUT/benchmark_results.json" \
  --dependency "$OUTPUT/dependency_analysis.json" \
  -o "$OUTPUT/experiment_report.md"
echo ""

echo "========================================="
echo "Workflow Complete!"
echo "========================================="
echo ""
echo "Results saved to: $OUTPUT/"
echo ""
echo "Generated files:"
ls -lh "$OUTPUT"
echo ""
echo "Report preview:"
head -30 "$OUTPUT/experiment_report.md"
