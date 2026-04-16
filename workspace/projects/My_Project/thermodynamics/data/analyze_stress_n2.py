import csv

with open('simulation_data_stress_hill_n2.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

data = {key: [float(row[key]) for row in rows] for key in rows[0].keys()}

print('='*80)
print('STRESS MODEL - HILL n=2 SIMULATION ANALYSIS')
print('='*80)

# Get column names
time_col = 'Time (s)'
atp_col = 'ATP_pool (mM)'
mature_col = 'Mature_spore (mM)'

print(f'\n1. SIMULATION PARAMETERS:')
print(f'   Time: {data[time_col][-1]:.1f}s, Data points: {len(rows)}')
print(f'   Initial ATP: {data[atp_col][0]:.1f} mM')

print(f'\n2. ATP DYNAMICS:')
print(f'   Initial ATP: {data[atp_col][0]:.1f} mM')
print(f'   Final ATP: {data[atp_col][-1]:.1f} mM')
print(f'   ATP change: {data[atp_col][-1] - data[atp_col][0]:+.1f} mM')
min_atp = min(data[atp_col])
min_idx = data[atp_col].index(min_atp)
print(f'   Minimum ATP: {min_atp:.2f} mM at t={data[time_col][min_idx]:.2f}s')
print(f'   ATP depletion: {(1 - min_atp/data[atp_col][0]) * 100:.1f}%')

mature_spores = data[mature_col][-1]
print(f'\n3. SPORULATION OUTCOME:')
print(f'   Final mature spores: {mature_spores:.2f} mM')
if mature_spores > 0:
    print(f'   Result: ✓ SUCCESS')
else:
    print(f'   Result: ✗ FAILURE (no spores produced)')

layers = [
    ('Spo0A_P (mM)', 'Layer 0 (Spo0A~P)'),
    ('SigmaH (mM)', 'Layer 1 (SigmaH)'),
    ('Septum (mM)', 'Layer 2 (Septum)'),
    ('SigmaF (mM)', 'Layer 3 (SigmaF)'),
    ('SigmaE (mM)', 'Layer 4 (SigmaE)'),
    ('SigmaG (mM)', 'Layer 5 (SigmaG)'),
    ('SigmaK (mM)', 'Layer 6 (SigmaK)')
]

print(f'\n4. HIERARCHICAL LAYER ACTIVATION:')
for col, name in layers:
    vals = data[col]
    act_time = None
    for i, v in enumerate(vals):
        if v > 0.1:
            act_time = data[time_col][i]
            break
    
    if act_time:
        print(f'   {name}: Activated at t={act_time:.3f}s (final: {vals[-1]:.2f} mM)')
    else:
        print(f'   {name}: NEVER activated (final: {vals[-1]:.2f} mM)')

# Transition firings
trans_cols = [col for col in data.keys() if col.startswith('T_') or col.startswith('Source_')]
print(f'\n5. KEY TRANSITION FIRINGS:')
key_trans = [
    'T_KinA_activation (firings)',
    'T_sigmaH_transcription (firings)',
    'T_septation (firings)',
    'T_sigmaF_activation (firings)',
    'T_sigmaE_feedback (firings)',
    'T_spore_maturation (firings)',
    'Source_ATP_regen (firings)'
]

for trans in key_trans:
    if trans in data:
        print(f'   {trans.replace(" (firings)", "")}: {data[trans][-1]:.1f} firings')

# ATP-dependent transitions total
atp_trans = [
    'T_KinA_activation (firings)',
    'T_sigmaH_transcription (firings)',
    'T_septation (firings)',
    'T_sigmaF_activation (firings)',
    'T_sigmaE_feedback (firings)',
    'T_sigmaG_transcription (firings)',
    'T_sigmaK_transcription (firings)',
    'T_forespore_formation (firings)',
    'T_mother_cell_formation (firings)',
    'T_cortex_synthesis (firings)',
    'T_inner_coat_synthesis (firings)',
    'T_spore_maturation (firings)'
]

total_atp_used = sum(data.get(t, [0])[-1] for t in atp_trans if t in data)
print(f'\n6. ATP CONSUMPTION:')
print(f'   Total ATP-dependent firings: {total_atp_used:.1f}')
if mature_spores > 0:
    print(f'   ATP economy: {total_atp_used/mature_spores:.1f} mM ATP/mM spore')

print('\n' + '='*80)
print('COMPARISON: NORMAL vs STRESS (Hill n=2)')
print('='*80)
print('\nNORMAL model (ATP=5000 mM initial):')
print('   - Final ATP: 14,571.9 mM (accumulated 3x!)')
print('   - Mature spores: 0.0 mM ✗ FAILURE')
print('   - Layers activated: Only SigmaE (anomalous)')
print('   - Problem: Hill n=2 blocks canonical pathway at high ATP')
print('\nSTRESS model (ATP=300 mM initial):')
print(f'   - Final ATP: {data[atp_col][-1]:.1f} mM')
print(f'   - Mature spores: {mature_spores:.2f} mM {"✓ SUCCESS" if mature_spores > 0 else "✗ FAILURE"}')
if mature_spores > 0:
    print(f'   - Bypass pathway WORKS with Hill n=2')
else:
    print(f'   - Bypass pathway ALSO BLOCKED by Hill n=2')
print('='*80)
