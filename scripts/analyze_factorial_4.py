#!/usr/bin/env python3
"""
Single Parameter Sweep Analysis for GATA1/PU1 Gene Regulatory Network
Analyzes EPO_external sweep with 4 levels: [0, 100, 250, 500]
This tests whether the balanced parameters from optimization are preserved
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Experiment directory
EXP_DIR = Path("workspace/projects/gata/experiments/factorial_4")

# EPO levels in the sweep
EPO_LEVELS = [0, 100, 250, 500]

print("=" * 80)
print("SINGLE PARAMETER SWEEP ANALYSIS - GATA1/PU1 GENE REGULATORY NETWORK")
print("EPO External Signal Sweep (GCSF=0)")
print("=" * 80)
print()
print("CONTEXT: This experiment was run AFTER parameter optimization to verify")
print("         that the viability panel correctly uses optimized parameters.")
print()
print("EXPECTED RESULTS (from optimized model):")
print("  - Nuclear proteins: 57-86 mM (physiological range)")
print("  - Cytoplasmic proteins: 800-1,000 mM")
print("  - ATP: ~51 mM")
print("  - GTP: ~5 mM")
print("  - Nuclear mRNA: 20-30 mM")
print("  - Cytoplasmic mRNA: 1,400-1,700 mM")
print("=" * 80)
print()

# Storage for results
results = []

for epo in EPO_LEVELS:
    filename = f"EPO_external_{epo}.csv"
    filepath = EXP_DIR / filename
    
    if not filepath.exists():
        print(f"⚠ Missing: {filename}")
        continue
    
    # Read the CSV file
    try:
        # Read file skipping metadata lines
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Find the header line (starts with "Time,")
        header_line_idx = None
        for i, line in enumerate(lines):
            if line.startswith('Time,'):
                header_line_idx = i
                break
        
        if header_line_idx is None:
            print(f"✗ Could not find header in {filename}")
            continue
        
        # Find where the data section ends (before "Trajectory Summary")
        data_end_idx = None
        for i in range(header_line_idx, len(lines)):
            if 'Trajectory Summary' in lines[i]:
                data_end_idx = i
                break
        
        if data_end_idx is None:
            data_end_idx = len(lines)  # Use entire file if no "Trajectory Summary" found
        
        # The header is split across two lines (line 7 and line 8)
        # Line 7: Time,P15,P16,...,P8
        # Line 8: data starts, but we need to extract remaining column names
        # Actually, looking at the structure, the data immediately follows the header
        # So we just need to read from header_line_idx to data_end_idx
        
        # Read only the data section
        section_lines = lines[header_line_idx:data_end_idx]
        
        # Parse with pandas
        from io import StringIO
        df = pd.read_csv(StringIO(''.join(section_lines)), low_memory=False)
        
        # Filter out non-numeric rows (last row might have text)
        # Keep only rows where Time is numeric
        df = df[pd.to_numeric(df['Time'], errors='coerce').notna()]
        
        # Get final values (last row with numeric data)
        final = df.iloc[-1]
        
        # Extract key species (convert to float to handle any string values)
        nuclear_gata1 = float(final.get('P9', 0))  # Nuclear GATA1
        nuclear_pu1 = float(final.get('P10', 0))   # Nuclear PU1
        cyto_gata1 = float(final.get('P11', 0))    # Cytoplasmic GATA1
        cyto_pu1 = float(final.get('P12', 0))      # Cytoplasmic PU1
        
        nuclear_gata1_mRNA = float(final.get('P17', 0))  # Nuclear GATA1 mRNA
        nuclear_pu1_mRNA = float(final.get('P18', 0))    # Nuclear PU1 mRNA
        cyto_gata1_mRNA = float(final.get('P13', 0))     # Cytoplasmic GATA1 mRNA
        cyto_pu1_mRNA = float(final.get('P14', 0))       # Cytoplasmic PU1 mRNA
        
        atp = float(final.get('P3', 0))
        gtp = float(final.get('P7', 0))
        
        # Calculate ratio
        ratio = nuclear_gata1 / nuclear_pu1 if nuclear_pu1 > 0 else float('inf')
        
        # Determine cell fate
        if ratio > 1.3:
            fate = "Erythroid"
        elif ratio < 0.7:
            fate = "Myeloid"
        else:
            fate = "Bistable"
        
        results.append({
            'EPO': epo,
            'Nuclear_GATA1': nuclear_gata1,
            'Nuclear_PU1': nuclear_pu1,
            'Cyto_GATA1': cyto_gata1,
            'Cyto_PU1': cyto_pu1,
            'Nuclear_GATA1_mRNA': nuclear_gata1_mRNA,
            'Nuclear_PU1_mRNA': nuclear_pu1_mRNA,
            'Cyto_GATA1_mRNA': cyto_gata1_mRNA,
            'Cyto_PU1_mRNA': cyto_pu1_mRNA,
            'GATA1_PU1_Ratio': ratio,
            'Cell_Fate': fate,
            'ATP': atp,
            'GTP': gtp
        })
        
        print(f"✓ Processed: EPO={epo}")
        
    except Exception as e:
        print(f"✗ Error processing {filename}: {e}")
        continue

print()
print("=" * 80)
print("RESULTS SUMMARY")
print("=" * 80)
print()

if not results:
    print("No results to display")
else:
    # Create DataFrame
    df_results = pd.DataFrame(results)
    
    # Display main results
    print("1. NUCLEAR PROTEIN LEVELS (mM)")
    print("-" * 80)
    print(f"{'EPO':>6} | {'Nuclear GATA1':>14} | {'Nuclear PU1':>12} | {'Ratio':>6} | {'Fate'}")
    print("-" * 80)
    for _, row in df_results.iterrows():
        print(f"{row['EPO']:>6.0f} | {row['Nuclear_GATA1']:>14.2f} | {row['Nuclear_PU1']:>12.2f} | {row['GATA1_PU1_Ratio']:>6.2f} | {row['Cell_Fate']}")
    print()
    
    print("2. CYTOPLASMIC PROTEIN LEVELS (mM)")
    print("-" * 80)
    print(f"{'EPO':>6} | {'Cyto GATA1':>11} | {'Cyto PU1':>9}")
    print("-" * 80)
    for _, row in df_results.iterrows():
        print(f"{row['EPO']:>6.0f} | {row['Cyto_GATA1']:>11.2f} | {row['Cyto_PU1']:>9.2f}")
    print()
    
    print("3. mRNA LEVELS (mM)")
    print("-" * 80)
    print(f"{'EPO':>6} | {'Nuclear GATA1 mRNA':>18} | {'Nuclear PU1 mRNA':>16} | {'Cyto GATA1 mRNA':>16} | {'Cyto PU1 mRNA':>14}")
    print("-" * 80)
    for _, row in df_results.iterrows():
        print(f"{row['EPO']:>6.0f} | {row['Nuclear_GATA1_mRNA']:>18.2f} | {row['Nuclear_PU1_mRNA']:>16.2f} | {row['Cyto_GATA1_mRNA']:>16.2f} | {row['Cyto_PU1_mRNA']:>14.2f}")
    print()
    
    print("4. ENERGY METABOLISM (mM)")
    print("-" * 80)
    print(f"{'EPO':>6} | {'ATP':>8} | {'GTP':>8}")
    print("-" * 80)
    for _, row in df_results.iterrows():
        print(f"{row['EPO']:>6.0f} | {row['ATP']:>8.2f} | {row['GTP']:>8.2f}")
    print()
    
    print("=" * 80)
    print("VALIDATION CHECK")
    print("=" * 80)
    print()
    
    # Check if results match expected optimized parameters
    nuclear_proteins_ok = all(
        50 <= row['Nuclear_GATA1'] <= 100 and 
        50 <= row['Nuclear_PU1'] <= 100 
        for _, row in df_results.iterrows()
    )
    
    energy_ok = all(
        40 <= row['ATP'] <= 60 and 
        3 <= row['GTP'] <= 10 
        for _, row in df_results.iterrows()
    )
    
    mRNA_ok = all(
        15 <= row['Nuclear_GATA1_mRNA'] <= 35 and
        15 <= row['Nuclear_PU1_mRNA'] <= 35 and
        1200 <= row['Cyto_GATA1_mRNA'] <= 1800 and
        1200 <= row['Cyto_PU1_mRNA'] <= 1800
        for _, row in df_results.iterrows()
    )
    
    print("Nuclear Proteins (50-100 mM expected):")
    if nuclear_proteins_ok:
        print("  ✓ PASS - All values in physiological range")
    else:
        print("  ✗ FAIL - Some values outside expected range")
        for _, row in df_results.iterrows():
            if not (50 <= row['Nuclear_GATA1'] <= 100 and 50 <= row['Nuclear_PU1'] <= 100):
                print(f"    EPO={row['EPO']}: GATA1={row['Nuclear_GATA1']:.1f}, PU1={row['Nuclear_PU1']:.1f}")
    print()
    
    print("Energy Metabolism (ATP: 40-60 mM, GTP: 3-10 mM expected):")
    if energy_ok:
        print("  ✓ PASS - All values in expected range")
    else:
        print("  ✗ FAIL - Some values outside expected range")
        for _, row in df_results.iterrows():
            if not (40 <= row['ATP'] <= 60 and 3 <= row['GTP'] <= 10):
                print(f"    EPO={row['EPO']}: ATP={row['ATP']:.1f}, GTP={row['GTP']:.1f}")
    print()
    
    print("mRNA Levels (Nuclear: 15-35 mM, Cyto: 1200-1800 mM expected):")
    if mRNA_ok:
        print("  ✓ PASS - All values in expected range")
    else:
        print("  ✗ FAIL - Some values outside expected range")
        for _, row in df_results.iterrows():
            if not (15 <= row['Nuclear_GATA1_mRNA'] <= 35 and 15 <= row['Nuclear_PU1_mRNA'] <= 35):
                print(f"    EPO={row['EPO']}: Nuclear GATA1 mRNA={row['Nuclear_GATA1_mRNA']:.1f}, Nuclear PU1 mRNA={row['Nuclear_PU1_mRNA']:.1f}")
            if not (1200 <= row['Cyto_GATA1_mRNA'] <= 1800 and 1200 <= row['Cyto_PU1_mRNA'] <= 1800):
                print(f"    EPO={row['EPO']}: Cyto GATA1 mRNA={row['Cyto_GATA1_mRNA']:.1f}, Cyto PU1 mRNA={row['Cyto_PU1_mRNA']:.1f}")
    print()
    
    print("=" * 80)
    print("OVERALL ASSESSMENT")
    print("=" * 80)
    print()
    
    if nuclear_proteins_ok and energy_ok and mRNA_ok:
        print("✓✓✓ SUCCESS ✓✓✓")
        print()
        print("The viability panel correctly uses OPTIMIZED parameters!")
        print("All species levels match the expected physiological ranges.")
        print()
        print("This confirms that the EventBus integration and parameter")
        print("refresh mechanisms are working correctly.")
    else:
        print("✗✗✗ VALIDATION FAILED ✗✗✗")
        print()
        print("Some species levels are outside expected ranges.")
        print("This may indicate:")
        print("  1. Parameter refresh mechanism not working")
        print("  2. Model parameters changed since optimization")
        print("  3. Different simulation conditions (time, termination)")
        print()
        print("Review the detailed results above to diagnose the issue.")
    
    print()
    print("=" * 80)
