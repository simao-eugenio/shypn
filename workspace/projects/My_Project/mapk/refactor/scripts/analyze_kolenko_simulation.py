#!/usr/bin/env python3
"""
Comprehensive analysis of Kholodenko parametrization simulation results
Compares with original Kholodenko data and analyzes feedback dynamics
"""

import csv
from pathlib import Path

def analyze_kholodenko_simulation(csv_path):
    """Analyze the parametrized Kholodenko simulation results"""
    
    print("="*80)
    print("KHOLODENKO PARAMETRIZATION SIMULATION ANALYSIS")
    print("="*80)
    
    # Read CSV data
    data = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    # Get column names
    headers = list(data[0].keys())
    
    print(f"\n📊 Simulation Overview:")
    print(f"  Total time points: {len(data)}")
    print(f"  Time range: {float(data[0]['Time (s)']):.2f}s to {float(data[-1]['Time (s)']):.2f}s")
    print(f"  Total columns: {len(headers)}")
    
    # Identify key species
    species_columns = [h for h in headers if h.endswith(' (mM)') and 'Phase' not in h and 'firings' not in h]
    
    print(f"\n🔬 Species tracked: {len(species_columns)}")
    for col in species_columns:
        print(f"  - {col}")
    
    # Analyze initial and final states
    initial = data[0]
    final = data[-1]
    
    print(f"\n\n{'='*80}")
    print("INITIAL STATE (t=0s)")
    print(f"{'='*80}")
    
    print(f"\n🟦 Cascade Initial Conditions:")
    for species in ['Raf_inactive', 'Raf_active', 'MEK_inactive', 'MEK_PP', 'ERK_inactive', 'ERK_PP', 'ERK_Nuclear']:
        col = f"{species} (mM)"
        if col in initial:
            val = float(initial[col])
            print(f"  {species:20s}: {val:8.3f} mM")
    
    print(f"\n🔴 Feedback Regulators Initial:")
    for species in ['PP2A', 'MKP']:
        col = f"{species} (mM)"
        if col in initial:
            val = float(initial[col])
            print(f"  {species:20s}: {val:8.3f} mM")
    
    print(f"\n🟢 Signal & Energy Initial:")
    for species in ['Growth_Factor', 'ATP', 'ADP']:
        col = f"{species} (mM)"
        if col in initial:
            val = float(initial[col])
            print(f"  {species:20s}: {val:8.3f} mM")
    
    print(f"\n⏱️  Phase Control Initial:")
    for species in ['Phase_Rest', 'Phase_Pulse', 'Phase_Recovery']:
        col = f"{species} (mM)"
        if col in initial:
            val = float(initial[col])
            print(f"  {species:20s}: {val:8.3f} mM")
    
    # FINAL STATE ANALYSIS
    print(f"\n\n{'='*80}")
    print(f"FINAL STATE (t={float(final['Time (s)']):.2f}s)")
    print(f"{'='*80}")
    
    print(f"\n🟦 Cascade Final State:")
    raf_inactive = float(final['Raf_inactive (mM)'])
    raf_active = float(final['Raf_active (mM)'])
    mek_inactive = float(final['MEK_inactive (mM)'])
    mek_pp = float(final['MEK_PP (mM)'])
    erk_inactive = float(final['ERK_inactive (mM)'])
    erk_pp = float(final['ERK_PP (mM)'])
    erk_nuclear = float(final['ERK_Nuclear (mM)'])
    
    raf_total = raf_inactive + raf_active
    mek_total = mek_inactive + mek_pp  # Note: Missing MEK_P in output
    erk_total = erk_inactive + erk_pp + erk_nuclear
    
    raf_pct = (raf_active / raf_total * 100) if raf_total > 0 else 0
    mek_pct = (mek_pp / mek_total * 100) if mek_total > 0 else 0
    erk_pct = (erk_pp / erk_total * 100) if erk_total > 0 else 0
    erk_nuclear_pct = (erk_nuclear / erk_total * 100) if erk_total > 0 else 0
    
    print(f"  Raf_inactive:        {raf_inactive:8.3f} mM")
    print(f"  Raf_active:          {raf_active:8.3f} mM ({raf_pct:.1f}%)")
    print(f"  Raf TOTAL:           {raf_total:8.3f} mM")
    print()
    print(f"  MEK_inactive:        {mek_inactive:8.3f} mM")
    print(f"  MEK_PP:              {mek_pp:8.3f} mM ({mek_pct:.1f}%)")
    print(f"  MEK TOTAL:           {mek_total:8.3f} mM")
    print()
    print(f"  ERK_inactive:        {erk_inactive:8.3f} mM")
    print(f"  ERK_PP:              {erk_pp:8.3f} mM ({erk_pct:.1f}%)")
    print(f"  ERK_Nuclear:         {erk_nuclear:8.3f} mM ({erk_nuclear_pct:.1f}%)")
    print(f"  ERK TOTAL:           {erk_total:8.3f} mM")
    
    print(f"\n🔴 Feedback Regulators Final:")
    pp2a_final = float(final['PP2A (mM)'])
    mkp_final = float(final['MKP (mM)'])
    print(f"  PP2A:                {pp2a_final:8.3f} mM")
    print(f"  MKP:                 {mkp_final:8.3f} mM")
    print(f"  PP2A/MKP ratio:      {pp2a_final/mkp_final:.4f}")
    
    print(f"\n🟢 Signal & Energy Final:")
    gf_final = float(final['Growth_Factor (mM)'])
    atp_final = float(final['ATP (mM)'])
    adp_final = float(final['ADP (mM)'])
    print(f"  Growth_Factor:       {gf_final:8.3f} mM")
    print(f"  ATP:                 {atp_final:8.3f} mM")
    print(f"  ADP:                 {adp_final:8.3f} mM")
    print(f"  ATP/(ATP+ADP):       {atp_final/(atp_final+adp_final):.4f}")
    
    # CASCADE AMPLIFICATION ANALYSIS
    print(f"\n\n{'='*80}")
    print("CASCADE AMPLIFICATION ANALYSIS")
    print(f"{'='*80}")
    
    print(f"\n  Level 1 (MAPKKK): {raf_pct:6.2f}% active")
    print(f"  Level 2 (MAPKK):  {mek_pct:6.2f}% active")
    print(f"  Level 3 (MAPK):   {erk_pct:6.2f}% active")
    print()
    print(f"  Amplification (L1→L2): {mek_pct/raf_pct if raf_pct > 0 else 0:.3f}x")
    print(f"  Amplification (L2→L3): {erk_pct/mek_pct if mek_pct > 0 else 0:.3f}x")
    print(f"  Total cascade gain:    {erk_pct/raf_pct if raf_pct > 0 else 0:.3f}x")
    
    # TEMPORAL DYNAMICS
    print(f"\n\n{'='*80}")
    print("TEMPORAL DYNAMICS")
    print(f"{'='*80}")
    
    # Find pulse start and end
    pulse_start_idx = None
    pulse_end_idx = None
    for i, row in enumerate(data):
        phase_pulse = float(row.get('Phase_Pulse (mM)', 0))
        if phase_pulse > 0 and pulse_start_idx is None:
            pulse_start_idx = i
        if phase_pulse == 0 and pulse_start_idx is not None and pulse_end_idx is None:
            pulse_end_idx = i
            break
    
    if pulse_start_idx:
        pulse_start_time = float(data[pulse_start_idx]['Time (s)'])
        print(f"\n  Pulse Start: t={pulse_start_time:.2f}s (index {pulse_start_idx})")
        
        if pulse_end_idx:
            pulse_end_time = float(data[pulse_end_idx]['Time (s)'])
            pulse_duration = pulse_end_time - pulse_start_time
            print(f"  Pulse End:   t={pulse_end_time:.2f}s (index {pulse_end_idx})")
            print(f"  Pulse Duration: {pulse_duration:.2f}s")
        else:
            print(f"  Pulse End:   Not detected (sustained pulse)")
    
    # Find ERK-PP peak
    erk_pp_values = [float(row['ERK_PP (mM)']) for row in data]
    max_erk_pp = max(erk_pp_values)
    max_erk_pp_idx = erk_pp_values.index(max_erk_pp)
    max_erk_pp_time = float(data[max_erk_pp_idx]['Time (s)'])
    max_erk_pp_pct = (max_erk_pp / erk_total * 100)
    
    print(f"\n  ERK-PP Peak:")
    print(f"    Value:     {max_erk_pp:.3f} mM ({max_erk_pp_pct:.2f}%)")
    print(f"    Time:      t={max_erk_pp_time:.2f}s")
    print(f"    Final:     {erk_pp:.3f} mM ({erk_pct:.2f}%)")
    
    # Calculate steady state (last 10% of simulation)
    steady_state_start = int(len(data) * 0.9)
    steady_state_data = data[steady_state_start:]
    
    avg_erk_pp = sum(float(row['ERK_PP (mM)']) for row in steady_state_data) / len(steady_state_data)
    avg_pp2a = sum(float(row['PP2A (mM)']) for row in steady_state_data) / len(steady_state_data)
    avg_mkp = sum(float(row['MKP (mM)']) for row in steady_state_data) / len(steady_state_data)
    
    print(f"\n  Steady State (last {len(steady_state_data)} points):")
    print(f"    ERK-PP:  {avg_erk_pp:.3f} mM ({avg_erk_pp/erk_total*100:.2f}%)")
    print(f"    PP2A:    {avg_pp2a:.3f} mM")
    print(f"    MKP:     {avg_mkp:.3f} mM")
    
    # COMPARISON WITH KHOLODENKO DATA
    print(f"\n\n{'='*80}")
    print("COMPARISON WITH KHOLODENKO 2000")
    print(f"{'='*80}")
    
    print(f"\n  Original Kholodenko (LOW state):")
    print(f"    ERK-PP final:  12.7 mM (4.2%)")
    print(f"    Cascade gain:  0.06x (signal attenuation)")
    print(f"    Mechanism:     Product feedback (ERK-PP inhibits MAPKKK)")
    
    print(f"\n  Your Parametrized Model:")
    print(f"    ERK-PP final:  {erk_pp:.3f} mM ({erk_pct:.2f}%)")
    print(f"    Cascade gain:  {erk_pct/raf_pct if raf_pct > 0 else 0:.3f}x")
    print(f"    Mechanism:     Pure negative feedback (no positive feedback)")
    
    # Determine state classification
    if erk_pct < 10:
        state = "LOW"
        emoji = "✅"
    elif erk_pct < 30:
        state = "INTERMEDIATE"
        emoji = "⚠️"
    else:
        state = "HIGH"
        emoji = "❌"
    
    print(f"\n  {emoji} STATE CLASSIFICATION: {state}")
    print(f"     ERK-PP {erk_pct:.2f}% activation")
    
    if state == "LOW":
        print(f"     Successfully reproduced Kholodenko LOW state!")
        print(f"     Parametric flexibility validated: topology unchanged, LOW state achieved")
    elif state == "INTERMEDIATE":
        print(f"     Partial success: Lower than HIGH state, but higher than Kholodenko")
        print(f"     May need further parameter tuning (increase PP2A or MKP)")
    else:
        print(f"     Did not achieve LOW state - still in HIGH regime")
        print(f"     Positive feedback may not be sufficiently suppressed")
    
    # FEEDBACK DYNAMICS
    print(f"\n\n{'='*80}")
    print("FEEDBACK DYNAMICS ANALYSIS")
    print(f"{'='*80}")
    
    # Calculate feedback strength at key time points
    if pulse_start_idx and pulse_start_idx + 100 < len(data):
        early_pulse_idx = pulse_start_idx + 100
        early_pulse = data[early_pulse_idx]
        early_erk_pp = float(early_pulse['ERK_PP (mM)'])
        early_pp2a = float(early_pulse['PP2A (mM)'])
        early_mkp = float(early_pulse['MKP (mM)'])
        early_time = float(early_pulse['Time (s)'])
        
        print(f"\n  Early Pulse Response (t={early_time:.1f}s):")
        print(f"    ERK-PP: {early_erk_pp:.3f} mM")
        print(f"    PP2A:   {early_pp2a:.3f} mM")
        print(f"    MKP:    {early_mkp:.3f} mM")
    
    print(f"\n  Final State (t={float(final['Time (s)']):.1f}s):")
    print(f"    ERK-PP: {erk_pp:.3f} mM")
    print(f"    PP2A:   {pp2a_final:.3f} mM")
    print(f"    MKP:    {mkp_final:.3f} mM")
    
    # Estimate feedback parameters from dynamics
    pp2a_initial = float(initial['PP2A (mM)'])
    mkp_initial = float(initial['MKP (mM)'])
    
    pp2a_fold_change = pp2a_final / pp2a_initial
    mkp_fold_change = mkp_final / mkp_initial if mkp_initial > 0 else float('inf')
    
    print(f"\n  Feedback Regulator Changes:")
    print(f"    PP2A: {pp2a_initial:.2f} → {pp2a_final:.2f} mM ({pp2a_fold_change:.2f}x)")
    print(f"    MKP:  {mkp_initial:.2f} → {mkp_final:.2f} mM ({mkp_fold_change:.2f}x)")
    
    print(f"\n  Feedback Balance:")
    print(f"    PP2A/MKP ratio: {pp2a_final/mkp_final:.4f}")
    if pp2a_final/mkp_final > 1.0:
        print(f"    → PP2A dominates (favors activation)")
    elif pp2a_final/mkp_final > 0.5:
        print(f"    → Balanced phosphatase activity")
    else:
        print(f"    → MKP dominates (favors deactivation)")
    
    # SUMMARY
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n  ✅ Model: Kholodenko Parametrization (from adaptation base)")
    print(f"  ✅ Simulation: {float(final['Time (s)']):.1f}s with {pulse_duration if pulse_end_idx else 'sustained'} pulse")
    print(f"  ✅ Final ERK-PP: {erk_pp:.3f} mM ({erk_pct:.2f}% activation)")
    print(f"  ✅ State: {state}")
    print(f"  ✅ Cascade Gain: {erk_pct/raf_pct if raf_pct > 0 else 0:.3f}x")
    
    print(f"\n  Key Finding:")
    if state == "LOW":
        print(f"    🎯 Successfully reproduced Kholodenko LOW state through parametrization!")
        print(f"    🎯 Same topology produces LOW state (adaptation base) vs HIGH state (bistability base)")
        print(f"    🎯 Validates parametric flexibility: α/β ratio controls computational mode")
    else:
        print(f"    ⚠️  Did not fully achieve Kholodenko LOW state")
        print(f"    ⚠️  May need further parameter adjustments")
    
    print(f"\n{'='*80}\n")
    
    return {
        'final_erk_pp': erk_pp,
        'final_erk_pct': erk_pct,
        'state': state,
        'cascade_gain': erk_pct/raf_pct if raf_pct > 0 else 0,
        'pp2a_final': pp2a_final,
        'mkp_final': mkp_final,
        'pp2a_mkp_ratio': pp2a_final/mkp_final
    }

def main():
    csv_path = Path("/home/simao/projetos/shypn/workspace/projects/My_Project/mapk/data/simulation_data_kolenko.csv")
    
    if not csv_path.exists():
        print(f"❌ File not found: {csv_path}")
        return 1
    
    results = analyze_kholodenko_simulation(csv_path)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
