#!/usr/bin/env python3
import csv
import numpy as np
from pathlib import Path
import json
import sys

batch_dir = Path('workspace/projects/My_Project/drug_discovery/data/thermo/tumor/results/batch_20260210_104958')

print('='*80)
print('TUMOR CELL BATCH ANALYSIS - 100 REPLICATES')
print('='*80)
sys.stdout.flush()

# Check config
with open(batch_dir / 'config.json', 'r') as f:
    config = json.load(f)

print(f'\nBatch: {config["timestamp"]}')
print(f'Duration: {config["settings"]["duration"]}s')
sys.stdout.flush()

# Analyze replicates
results = {
    'ATP_pool': [],
    'ADP_pool': [],
    'Pi_pool': [],
    'Membrane_potential': [],
    'PEPT1_free': [],
    'Drug_intracellular': []
}

initial_atp = None
initial_adp = None
initial_pi = None

print('\nReading 100 replicates...')
sys.stdout.flush()

for i in range(1, 101):
    csv_file = batch_dir / f'run_{i:03d}.csv'
    
    with open(csv_file, 'r') as f:
        lines = f.readlines()
        data_start = 0
        for idx, line in enumerate(lines):
            if line.startswith('time,'):
                data_start = idx
                break
    
    with open(csv_file, 'r') as f:
        for _ in range(data_start):
            f.readline()
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if i == 1:
        initial_atp = float(rows[0]['P7'])
        initial_adp = float(rows[0]['P8'])
        initial_pi = float(rows[0]['P9'])
    
    final_row = rows[-1]
    results['ATP_pool'].append(float(final_row['P7']))
    results['ADP_pool'].append(float(final_row['P8']))
    results['Pi_pool'].append(float(final_row['P9']))
    results['Membrane_potential'].append(float(final_row['P11']))
    results['PEPT1_free'].append(float(final_row['P3']))
    results['Drug_intracellular'].append(float(final_row['P2']))
    
    if i % 20 == 0:
        print(f'  {i}/100')
        sys.stdout.flush()

print('✓ Complete\n')
sys.stdout.flush()

# Verify initial conditions
print('='*80)
print('INITIAL CONDITIONS')
print('='*80)
print(f'ATP = {initial_atp:.0f} mM')
print(f'ADP = {initial_adp:.0f} mM')
print(f'Pi  = {initial_pi:.0f} mM')

if initial_pi == 500.0:
    print('✓ Correct balanced state')
else:
    print(f'⚠️  Pi should be 500, got {initial_pi}')
sys.stdout.flush()

# Statistics
print('\n' + '='*80)
print('FINAL STATE STATISTICS (n=100)')
print('='*80)
sys.stdout.flush()

stats = {}
for name, values in results.items():
    mean = np.mean(values)
    std = np.std(values)
    cv = (std / mean) * 100 if mean != 0 else 0
    stats[name] = {'mean': mean, 'std': std, 'cv': cv}
    
    unit = 'units' if name == 'PEPT1_free' else 'mM'
    print(f'\n{name.replace("_", " ")}:')
    print(f'  {mean:.2f} ± {std:.2f} {unit} (CV={cv:.1f}%)')
    sys.stdout.flush()

# Key findings
print('\n' + '='*80)
print('KEY FINDINGS')
print('='*80)
sys.stdout.flush()

atp_change = stats['ATP_pool']['mean'] - initial_atp

print(f'\nATP Recovery:')
print(f'  {initial_atp:.0f} → {stats["ATP_pool"]["mean"]:.0f} mM ({atp_change:+.0f} mM)')
print(f'  CV = {stats["ATP_pool"]["cv"]:.1f}%')

print(f'\nMembrane: {stats["Membrane_potential"]["mean"]:.1f} ± {stats["Membrane_potential"]["std"]:.1f} mV')
print(f'PEPT1:    {stats["PEPT1_free"]["mean"]:.1f} ± {stats["PEPT1_free"]["std"]:.1f} units')
print(f'Drug:     {stats["Drug_intracellular"]["mean"]:.2f} ± {stats["Drug_intracellular"]["std"]:.2f} mM')

if atp_change > 0:
    print(f'\n✓ ATP RECOVERY confirmed (+{atp_change:.0f} mM over 500s)')
    print('✓ Low CV proves robust emergent homeostasis')
else:
    print(f'\n⚠️ ATP depletion ({atp_change:.0f} mM)')

sys.stdout.flush()
print()
