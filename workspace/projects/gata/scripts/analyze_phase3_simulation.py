#!/usr/bin/env python3
"""
Analyze Phase 3A Simulation Results

Checks for:
1. Steady state achievement
2. ATP/GTP balance
3. GATA1 vs PU1 commitment dynamics
4. Spatial signal levels
5. Receptor dynamics

Date: 2026-02-17
"""

import csv
import statistics
from pathlib import Path

def analyze_simulation():
    """Comprehensive analysis of Phase 3A simulation results"""
    
    data_path = Path("workspace/projects/gata/data/simulation_data.csv")
    
    print("=" * 70)
    print("PHASE 3A SIMULATION ANALYSIS")
    print("=" * 70)
    print()
    
    # Load data
    with open(data_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"✅ Data loaded: {len(rows)} time points")
    print(f"   Duration: {float(rows[0]['Time (s)']):.1f}s - {float(rows[-1]['Time (s)']):.1f}s")
    print(f"   Variables: {len(rows[0])} tracked")
    print()
    
    # ========================================================================
    # 1. LINEAGE COMMITMENT ANALYSIS
    # ========================================================================
    print("=" * 70)
    print("1. LINEAGE COMMITMENT ANALYSIS")
    print("=" * 70)
    
    # Get final values
    final = rows[-1]
    
    # Nuclear transcription factors (decision makers)
    gata1_nuc = float(final['GATA1_Protein_nuc (mM)'])
    pu1_nuc = float(final['PU1_Protein_nuc (mM)'])
    
    # Cytoplasmic proteins
    gata1_cyto = float(final['GATA1_Protein_cyto (mM)'])
    pu1_cyto = float(final['PU1_Protein_cyto (mM)'])
    
    print(f"\n📊 FINAL STATE (t={float(final['Time (s)']):.1f}s):")
    print(f"   Nuclear GATA1:  {gata1_nuc:8.2f} mM")
    print(f"   Nuclear PU.1:   {pu1_nuc:8.2f} mM")
    print(f"   Ratio (GATA1/PU1): {gata1_nuc/pu1_nuc:.2f}")
    print()
    print(f"   Cytoplasmic GATA1: {gata1_cyto:8.2f} mM")
    print(f"   Cytoplasmic PU.1:  {pu1_cyto:8.2f} mM")
    print()
    
    # Determine commitment
    if gata1_nuc > 100 * pu1_nuc:
        commitment = "GATA1+ (Erythroid)"
        print(f"   🔴 COMMITMENT: {commitment}")
    elif pu1_nuc > 100 * gata1_nuc:
        commitment = "PU.1+ (Myeloid)"
        print(f"   ⚪ COMMITMENT: {commitment}")
    else:
        commitment = "Bistable/Undecided"
        print(f"   ⚖️  COMMITMENT: {commitment}")
    print()
    
    # ========================================================================
    # 2. STEADY STATE ANALYSIS
    # ========================================================================
    print("=" * 70)
    print("2. STEADY STATE ANALYSIS")
    print("=" * 70)
    
    # Check last 20% of simulation for steady state
    max_time = float(rows[-1]['Time (s)'])
    cutoff_time = max_time * 0.8
    steady_window = [r for r in rows if float(r['Time (s)']) > cutoff_time]
    
    # Calculate coefficient of variation (CV) for key species
    print("\n📈 Coefficient of Variation (last 20% of simulation):")
    print("   (CV < 0.05 indicates steady state)\n")
    
    key_species = [
        'GATA1_Protein_nuc (mM)',
        'PU1_Protein_nuc (mM)',
        'GATA1_mRNA_cyto (mM)',
        'PU1_mRNA_cyto (mM)',
        'ATP (mM)',
        'GTP (mM)'
    ]
    
    steady_state = True
    for species in key_species:
        values = [float(r[species]) for r in steady_window]
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        cv = std_val / mean_val if mean_val > 0 else float('inf')
        
        status = "✅" if cv < 0.05 else "⚠️" if cv < 0.1 else "❌"
        print(f"   {status} {species:30s}: CV = {cv:.4f}")
        
        if cv >= 0.1:
            steady_state = False
    
    print()
    if steady_state:
        print("   ✅ STEADY STATE ACHIEVED")
    else:
        print("   ⚠️  Some species still fluctuating")
    print()
    
    # ========================================================================
    # 3. ENERGY BALANCE (ATP/GTP)
    # ========================================================================
    print("=" * 70)
    print("3. ENERGY BALANCE")
    print("=" * 70)
    
    atp_final = float(final['ATP (mM)'])
    adp_final = float(final['ADP (mM)'])
    gtp_final = float(final['GTP (mM)'])
    gdp_final = float(final['GDP (mM)'])
    pi_final = float(final['Pi (mM)'])
    
    # Check conservation
    atp_total_initial = float(rows[0]['ATP (mM)']) + float(rows[0]['ADP (mM)'])
    atp_total_final = atp_final + adp_final
    
    gtp_total_initial = float(rows[0]['GTP (mM)']) + float(rows[0]['GDP (mM)'])
    gtp_total_final = gtp_final + gdp_final
    
    print(f"\n⚡ ATP SYSTEM:")
    print(f"   ATP: {atp_final:8.2f} mM")
    print(f"   ADP: {adp_final:8.2f} mM")
    print(f"   Total: {atp_total_final:8.2f} mM (initial: {atp_total_initial:.2f})")
    print(f"   Energy charge: {atp_final / atp_total_final:.3f}")
    print()
    
    print(f"🔋 GTP SYSTEM:")
    print(f"   GTP: {gtp_final:8.2f} mM")
    print(f"   GDP: {gdp_final:8.2f} mM")
    print(f"   Total: {gtp_total_final:8.2f} mM (initial: {gtp_total_initial:.2f})")
    print(f"   Energy charge: {gtp_final / gtp_total_final:.3f}")
    print()
    
    print(f"💊 PHOSPHATE:")
    print(f"   Pi: {pi_final:8.2f} mM")
    print()
    
    # Check if energy is maintained
    if atp_final / atp_total_final > 0.7 and gtp_final / gtp_total_final > 0.7:
        print("   ✅ ENERGY BALANCE MAINTAINED (high energy charge)")
    elif atp_final / atp_total_final > 0.3 and gtp_final / gtp_total_final > 0.3:
        print("   ⚠️  Energy charge moderate")
    else:
        print("   ❌ Energy depleted!")
    print()
    
    # ========================================================================
    # 4. SPATIAL SIGNALS
    # ========================================================================
    print("=" * 70)
    print("4. SPATIAL SIGNAL LEVELS")
    print("=" * 70)
    
    epo_final = float(final['EPO_external (mM)'])
    gcsf_final = float(final['GCSF_external (mM)'])
    
    print(f"\n🌐 EXTRACELLULAR SIGNALS:")
    print(f"   EPO:  {epo_final:8.2f} mM")
    print(f"   GCSF: {gcsf_final:8.2f} mM")
    print(f"   Signal ratio (EPO/GCSF): {epo_final/gcsf_final if gcsf_final > 0 else 'inf'}")
    print()
    
    # ========================================================================
    # 5. RECEPTOR DYNAMICS
    # ========================================================================
    print("=" * 70)
    print("5. RECEPTOR DYNAMICS")
    print("=" * 70)
    
    epor_free = float(final['EPOR_free (mM)'])
    epor_bound = float(final['EPOR_bound (mM)'])
    epor_intern = float(final['EPOR_internalized (mM)'])
    
    gcsfr_free = float(final['GCSFR_free (mM)'])
    gcsfr_bound = float(final['GCSFR_bound (mM)'])
    gcsfr_intern = float(final['GCSFR_internalized (mM)'])
    
    print(f"\n🔴 EPO RECEPTOR:")
    print(f"   Free:         {epor_free:8.2f} mM")
    print(f"   Bound:        {epor_bound:8.2f} mM")
    print(f"   Internalized: {epor_intern:8.2f} mM")
    print(f"   Total: {epor_free + epor_bound + epor_intern:8.2f} mM")
    print(f"   Occupancy: {epor_bound / (epor_free + epor_bound):.1%}" if (epor_free + epor_bound) > 0 else "   Occupancy: N/A")
    print()
    
    print(f"⚪ GCSF RECEPTOR:")
    print(f"   Free:         {gcsfr_free:8.2f} mM")
    print(f"   Bound:        {gcsfr_bound:8.2f} mM")
    print(f"   Internalized: {gcsfr_intern:8.2f} mM")
    print(f"   Total: {gcsfr_free + gcsfr_bound + gcsfr_intern:8.2f} mM")
    print(f"   Occupancy: {gcsfr_bound / (gcsfr_free + gcsfr_bound):.1%}" if (gcsfr_free + gcsfr_bound) > 0 else "   Occupancy: N/A")
    print()
    
    # ========================================================================
    # 6. TRANSCRIPTION ACTIVITY
    # ========================================================================
    print("=" * 70)
    print("6. TRANSCRIPTION ACTIVITY")
    print("=" * 70)
    
    gata1_transcription_fires = float(final['GATA1_transcription (firings)'])
    pu1_transcription_fires = float(final['PU1_transcription (firings)'])
    
    print(f"\n📝 CUMULATIVE TRANSCRIPTION EVENTS:")
    print(f"   GATA1: {gata1_transcription_fires:8.0f} firings")
    print(f"   PU.1:  {pu1_transcription_fires:8.0f} firings")
    print(f"   Ratio: {gata1_transcription_fires / pu1_transcription_fires if pu1_transcription_fires > 0 else 'inf':.2f}")
    print()
    
    # ========================================================================
    # 7. mRNA LEVELS
    # ========================================================================
    print("=" * 70)
    print("7. mRNA LEVELS")
    print("=" * 70)
    
    gata1_mrna_nuc = float(final['GATA1_mRNA_nuc (mM)'])
    pu1_mrna_nuc = float(final['PU1_mRNA_nuc (mM)'])
    gata1_mrna_cyto = float(final['GATA1_mRNA_cyto (mM)'])
    pu1_mrna_cyto = float(final['PU1_mRNA_cyto (mM)'])
    
    print(f"\n🧬 NUCLEAR mRNA:")
    print(f"   GATA1: {gata1_mrna_nuc:8.2f} mM")
    print(f"   PU.1:  {pu1_mrna_nuc:8.2f} mM")
    print()
    
    print(f"🧬 CYTOPLASMIC mRNA:")
    print(f"   GATA1: {gata1_mrna_cyto:8.2f} mM")
    print(f"   PU.1:  {pu1_mrna_cyto:8.2f} mM")
    print()
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"✅ Simulation completed: {float(final['Time (s)']):.1f}s")
    print(f"✅ Lineage commitment: {commitment}")
    print(f"✅ Steady state: {'Achieved' if steady_state else 'Not fully achieved'}")
    print(f"✅ Energy balance: ATP charge = {atp_final / atp_total_final:.1%}, GTP charge = {gtp_final / gtp_total_final:.1%}")
    print(f"✅ Signal levels: EPO = {epo_final:.1f} mM, GCSF = {gcsf_final:.1f} mM")
    print()
    
    # Key insights
    print("=" * 70)
    print("KEY INSIGHTS")
    print("=" * 70)
    print()
    
    if gata1_nuc > 100 * pu1_nuc:
        print("1. Cell committed to ERYTHROID lineage (GATA1+ dominance)")
        print(f"   - Nuclear GATA1 >> PU.1 ({gata1_nuc:.1f} vs {pu1_nuc:.1f})")
        print(f"   - GATA1 transcription highly active ({gata1_transcription_fires:.0f} events)")
    elif pu1_nuc > 100 * gata1_nuc:
        print("1. Cell committed to MYELOID lineage (PU.1+ dominance)")
        print(f"   - Nuclear PU.1 >> GATA1 ({pu1_nuc:.1f} vs {gata1_nuc:.1f})")
        print(f"   - PU.1 transcription highly active ({pu1_transcription_fires:.0f} events)")
    else:
        print("1. Cell in BISTABLE state (both factors present)")
        print(f"   - GATA1 and PU.1 coexist at similar levels")
        print(f"   - May resolve with longer simulation time")
    print()
    
    if epo_final > 10 * gcsf_final:
        print("2. EPO signal dominates → Favors erythroid commitment")
    elif gcsf_final > 10 * epo_final:
        print("2. GCSF signal dominates → Favors myeloid commitment")
    else:
        print("2. Mixed signal environment → Bistable competition")
    print()
    
    print("3. Adaptive transitions (transcription):")
    print("   - Expected to use STOCHASTIC mode (nucleus 0.5 fL < 1.0 fL threshold)")
    print("   - Check console logs for mode switching confirmation")
    print()
    
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    analyze_simulation()
    
    # ========================================================================
    # 1. LINEAGE COMMITMENT ANALYSIS
    # ========================================================================
    print("=" * 70)
    print("1. LINEAGE COMMITMENT ANALYSIS")
    print("=" * 70)
    
    # Get final values
    final = df.iloc[-1]
    
    # Nuclear transcription factors (decision makers)
    gata1_nuc = final['GATA1_Protein_nuc (mM)']
    pu1_nuc = final['PU1_Protein_nuc (mM)']
    
    # Cytoplasmic proteins
    gata1_cyto = final['GATA1_Protein_cyto (mM)']
    pu1_cyto = final['PU1_Protein_cyto (mM)']
    
    print(f"\n📊 FINAL STATE (t={final['Time (s)']:.1f}s):")
    print(f"   Nuclear GATA1:  {gata1_nuc:8.2f} mM")
    print(f"   Nuclear PU.1:   {pu1_nuc:8.2f} mM")
    print(f"   Ratio (GATA1/PU1): {gata1_nuc/pu1_nuc:.2f}")
    print()
    print(f"   Cytoplasmic GATA1: {gata1_cyto:8.2f} mM")
    print(f"   Cytoplasmic PU.1:  {pu1_cyto:8.2f} mM")
    print()
    
    # Determine commitment
    if gata1_nuc > 100 * pu1_nuc:
        commitment = "GATA1+ (Erythroid)"
        print(f"   🔴 COMMITMENT: {commitment}")
    elif pu1_nuc > 100 * gata1_nuc:
        commitment = "PU.1+ (Myeloid)"
        print(f"   ⚪ COMMITMENT: {commitment}")
    else:
        commitment = "Bistable/Undecided"
        print(f"   ⚖️  COMMITMENT: {commitment}")
    print()
    
    # ========================================================================
    # 2. STEADY STATE ANALYSIS
    # ========================================================================
    print("=" * 70)
    print("2. STEADY STATE ANALYSIS")
    print("=" * 70)
    
    # Check last 20% of simulation for steady state
    steady_window = df[df['Time (s)'] > df['Time (s)'].max() * 0.8]
    
    # Calculate coefficient of variation (CV) for key species
    print("\n📈 Coefficient of Variation (last 20% of simulation):")
    print("   (CV < 0.05 indicates steady state)\n")
    
    key_species = [
        'GATA1_Protein_nuc (mM)',
        'PU1_Protein_nuc (mM)',
        'GATA1_mRNA_cyto (mM)',
        'PU1_mRNA_cyto (mM)',
        'ATP (mM)',
        'GTP (mM)'
    ]
    
    steady_state = True
    for species in key_species:
        if species in steady_window.columns:
            mean_val = steady_window[species].mean()
            std_val = steady_window[species].std()
            cv = std_val / mean_val if mean_val > 0 else np.inf
            
            status = "✅" if cv < 0.05 else "⚠️" if cv < 0.1 else "❌"
            print(f"   {status} {species:30s}: CV = {cv:.4f}")
            
            if cv >= 0.1:
                steady_state = False
    
    print()
    if steady_state:
        print("   ✅ STEADY STATE ACHIEVED")
    else:
        print("   ⚠️  Some species still fluctuating")
    print()
    
    # ========================================================================
    # 3. ENERGY BALANCE (ATP/GTP)
    # ========================================================================
    print("=" * 70)
    print("3. ENERGY BALANCE")
    print("=" * 70)
    
    atp_final = final['ATP (mM)']
    adp_final = final['ADP (mM)']
    gtp_final = final['GTP (mM)']
    gdp_final = final['GDP (mM)']
    pi_final = final['Pi (mM)']
    
    # Check conservation
    atp_total_initial = df.iloc[0]['ATP (mM)'] + df.iloc[0]['ADP (mM)']
    atp_total_final = atp_final + adp_final
    
    gtp_total_initial = df.iloc[0]['GTP (mM)'] + df.iloc[0]['GDP (mM)']
    gtp_total_final = gtp_final + gdp_final
    
    print(f"\n⚡ ATP SYSTEM:")
    print(f"   ATP: {atp_final:8.2f} mM")
    print(f"   ADP: {adp_final:8.2f} mM")
    print(f"   Total: {atp_total_final:8.2f} mM (initial: {atp_total_initial:.2f})")
    print(f"   Energy charge: {atp_final / atp_total_final:.3f}")
    print()
    
    print(f"🔋 GTP SYSTEM:")
    print(f"   GTP: {gtp_final:8.2f} mM")
    print(f"   GDP: {gdp_final:8.2f} mM")
    print(f"   Total: {gtp_total_final:8.2f} mM (initial: {gtp_total_initial:.2f})")
    print(f"   Energy charge: {gtp_final / gtp_total_final:.3f}")
    print()
    
    print(f"💊 PHOSPHATE:")
    print(f"   Pi: {pi_final:8.2f} mM")
    print()
    
    # Check if energy is maintained
    if atp_final / atp_total_final > 0.7 and gtp_final / gtp_total_final > 0.7:
        print("   ✅ ENERGY BALANCE MAINTAINED (high energy charge)")
    elif atp_final / atp_total_final > 0.3 and gtp_final / gtp_total_final > 0.3:
        print("   ⚠️  Energy charge moderate")
    else:
        print("   ❌ Energy depleted!")
    print()
    
    # ========================================================================
    # 4. SPATIAL SIGNALS
    # ========================================================================
    print("=" * 70)
    print("4. SPATIAL SIGNAL LEVELS")
    print("=" * 70)
    
    epo_final = final['EPO_external (mM)']
    gcsf_final = final['GCSF_external (mM)']
    
    print(f"\n🌐 EXTRACELLULAR SIGNALS:")
    print(f"   EPO:  {epo_final:8.2f} mM")
    print(f"   GCSF: {gcsf_final:8.2f} mM")
    print(f"   Signal ratio (EPO/GCSF): {epo_final/gcsf_final if gcsf_final > 0 else 'inf'}")
    print()
    
    # ========================================================================
    # 5. RECEPTOR DYNAMICS
    # ========================================================================
    print("=" * 70)
    print("5. RECEPTOR DYNAMICS")
    print("=" * 70)
    
    epor_free = final['EPOR_free (mM)']
    epor_bound = final['EPOR_bound (mM)']
    epor_intern = final['EPOR_internalized (mM)']
    
    gcsfr_free = final['GCSFR_free (mM)']
    gcsfr_bound = final['GCSFR_bound (mM)']
    gcsfr_intern = final['GCSFR_internalized (mM)']
    
    print(f"\n🔴 EPO RECEPTOR:")
    print(f"   Free:         {epor_free:8.2f} mM")
    print(f"   Bound:        {epor_bound:8.2f} mM")
    print(f"   Internalized: {epor_intern:8.2f} mM")
    print(f"   Total: {epor_free + epor_bound + epor_intern:8.2f} mM")
    print(f"   Occupancy: {epor_bound / (epor_free + epor_bound):.1%}" if (epor_free + epor_bound) > 0 else "   Occupancy: N/A")
    print()
    
    print(f"⚪ GCSF RECEPTOR:")
    print(f"   Free:         {gcsfr_free:8.2f} mM")
    print(f"   Bound:        {gcsfr_bound:8.2f} mM")
    print(f"   Internalized: {gcsfr_intern:8.2f} mM")
    print(f"   Total: {gcsfr_free + gcsfr_bound + gcsfr_intern:8.2f} mM")
    print(f"   Occupancy: {gcsfr_bound / (gcsfr_free + gcsfr_bound):.1%}" if (gcsfr_free + gcsfr_bound) > 0 else "   Occupancy: N/A")
    print()
    
    # ========================================================================
    # 6. TRANSCRIPTION ACTIVITY
    # ========================================================================
    print("=" * 70)
    print("6. TRANSCRIPTION ACTIVITY")
    print("=" * 70)
    
    gata1_transcription_fires = final['GATA1_transcription (firings)']
    pu1_transcription_fires = final['PU1_transcription (firings)']
    
    print(f"\n📝 CUMULATIVE TRANSCRIPTION EVENTS:")
    print(f"   GATA1: {gata1_transcription_fires:8.0f} firings")
    print(f"   PU.1:  {pu1_transcription_fires:8.0f} firings")
    print(f"   Ratio: {gata1_transcription_fires / pu1_transcription_fires if pu1_transcription_fires > 0 else 'inf':.2f}")
    print()
    
    # ========================================================================
    # 7. mRNA LEVELS
    # ========================================================================
    print("=" * 70)
    print("7. mRNA LEVELS")
    print("=" * 70)
    
    gata1_mrna_nuc = final['GATA1_mRNA_nuc (mM)']
    pu1_mrna_nuc = final['PU1_mRNA_nuc (mM)']
    gata1_mrna_cyto = final['GATA1_mRNA_cyto (mM)']
    pu1_mrna_cyto = final['PU1_mRNA_cyto (mM)']
    
    print(f"\n🧬 NUCLEAR mRNA:")
    print(f"   GATA1: {gata1_mrna_nuc:8.2f} mM")
    print(f"   PU.1:  {pu1_mrna_nuc:8.2f} mM")
    print()
    
    print(f"🧬 CYTOPLASMIC mRNA:")
    print(f"   GATA1: {gata1_mrna_cyto:8.2f} mM")
    print(f"   PU.1:  {pu1_mrna_cyto:8.2f} mM")
    print()
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"✅ Simulation completed: {final['Time (s)']:.1f}s")
    print(f"✅ Lineage commitment: {commitment}")
    print(f"✅ Steady state: {'Achieved' if steady_state else 'Not fully achieved'}")
    print(f"✅ Energy balance: ATP charge = {atp_final / atp_total_final:.1%}, GTP charge = {gtp_final / gtp_total_final:.1%}")
    print(f"✅ Signal levels: EPO = {epo_final:.1f} mM, GCSF = {gcsf_final:.1f} mM")
    print()
    
    # Key insights
    print("=" * 70)
    print("KEY INSIGHTS")
    print("=" * 70)
    print()
    
    if gata1_nuc > 100 * pu1_nuc:
        print("1. Cell committed to ERYTHROID lineage (GATA1+ dominance)")
        print(f"   - Nuclear GATA1 >> PU.1 ({gata1_nuc:.1f} vs {pu1_nuc:.1f})")
        print(f"   - GATA1 transcription highly active ({gata1_transcription_fires:.0f} events)")
    elif pu1_nuc > 100 * gata1_nuc:
        print("1. Cell committed to MYELOID lineage (PU.1+ dominance)")
        print(f"   - Nuclear PU.1 >> GATA1 ({pu1_nuc:.1f} vs {gata1_nuc:.1f})")
        print(f"   - PU.1 transcription highly active ({pu1_transcription_fires:.0f} events)")
    else:
        print("1. Cell in BISTABLE state (both factors present)")
        print(f"   - GATA1 and PU.1 coexist at similar levels")
        print(f"   - May resolve with longer simulation time")
    print()
    
    if epo_final > 10 * gcsf_final:
        print("2. EPO signal dominates → Favors erythroid commitment")
    elif gcsf_final > 10 * epo_final:
        print("2. GCSF signal dominates → Favors myeloid commitment")
    else:
        print("2. Mixed signal environment → Bistable competition")
    print()
    
    print("3. Adaptive transitions (transcription):")
    print("   - Expected to use STOCHASTIC mode (nucleus 0.5 fL < 1.0 fL threshold)")
    print("   - Check console logs for mode switching confirmation")
    print()
    
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    analyze_simulation()
