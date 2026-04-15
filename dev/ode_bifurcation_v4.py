#!/usr/bin/env python3
"""
ODE (mean-field) bifurcation analysis for phase3a_spatial_clean_v4.shy.

Solves the deterministic equivalent of all 32 transitions using scipy solve_ivp.
Rate functions are transcribed directly from the model JSON — no model file is
modified. Run a sweep over EPO_external at fixed GCSF=0.001 mM and report the
steady-state GATA1/PU1 ratio to find the bifurcation point.

Usage:
    python dev/ode_bifurcation_v4.py
"""
import numpy as np
from scipy.integrate import solve_ivp
import warnings

# ── Fixed model parameters ────────────────────────────────────────────────────
T        = 310.15   # K  (A3 axiom)
pH_nuc   = 7.5
pH_cyto  = 7.4
Mg_cyto  = 0.5      # mM
ATP0     = 3000.0   # mM (buffered)
ADP0     = 300.0    # mM (buffered)
GTP0     = 300.0    # mM (buffered)
GDP0     = 30.0     # mM (buffered)
Pi0      = 10.0     # mM (buffered)

RU = np.exp  # shorthand

# ── State vector index map ─────────────────────────────────────────────────────
IDX = {
    'EPO_external':       0,
    'GCSF_external':      1,
    'EPOR_free':          2,
    'EPOR_bound':         3,
    'EPOR_internalized':  4,
    'GCSFR_free':         5,
    'GCSFR_bound':        6,
    'GCSFR_internalized': 7,
    'GATA1_mRNA_nuc':     8,
    'PU1_mRNA_nuc':       9,
    'GATA1_mRNA_cyto':   10,
    'PU1_mRNA_cyto':     11,
    'GATA1_Protein_cyto':12,
    'PU1_Protein_cyto':  13,
    'GATA1_Protein_nuc': 14,
    'PU1_Protein_nuc':   15,
    'pGATA1_nuc':        16,
    'pPU1_nuc':          17,
    'GATA1_Gene':        18,
    'PU1_Gene':          19,
}
N = len(IDX)

# ── Default initial conditions ────────────────────────────────────────────────
DEFAULT_ICS = {
    'EPO_external':       1.0,
    'GCSF_external':      0.001,
    'EPOR_free':          4.2,
    'EPOR_bound':         0.49,
    'EPOR_internalized':  0.0,
    'GCSFR_free':         4.1,
    'GCSFR_bound':        0.47,
    'GCSFR_internalized': 0.0,
    'GATA1_mRNA_nuc':     1.0,
    'PU1_mRNA_nuc':       1.0,
    'GATA1_mRNA_cyto':    1.0,
    'PU1_mRNA_cyto':      1.0,
    'GATA1_Protein_cyto': 1.0,
    'PU1_Protein_cyto':   1.0,
    'GATA1_Protein_nuc':  1.0,
    'PU1_Protein_nuc':    1.0,
    'pGATA1_nuc':         0.39,
    'pPU1_nuc':           0.3806,
    'GATA1_Gene':         1.0,
    'PU1_Gene':           1.0,
}

def make_ics(**overrides):
    ics = dict(DEFAULT_ICS)
    ics.update(overrides)
    return np.array([ics[k] for k in IDX])


# ── ODE right-hand side ────────────────────────────────────────────────────────
def odes(t, y):
    # Unpack state
    EPO         = max(y[IDX['EPO_external']], 0)
    GCSF        = max(y[IDX['GCSF_external']], 0)
    EPOR_f      = max(y[IDX['EPOR_free']], 0)
    EPOR_b      = max(y[IDX['EPOR_bound']], 0)
    EPOR_i      = max(y[IDX['EPOR_internalized']], 0)
    GCSFR_f     = max(y[IDX['GCSFR_free']], 0)
    GCSFR_b     = max(y[IDX['GCSFR_bound']], 0)
    GCSFR_i     = max(y[IDX['GCSFR_internalized']], 0)
    G1mRNA_n    = max(y[IDX['GATA1_mRNA_nuc']], 0)
    P1mRNA_n    = max(y[IDX['PU1_mRNA_nuc']], 0)
    G1mRNA_c    = max(y[IDX['GATA1_mRNA_cyto']], 0)
    P1mRNA_c    = max(y[IDX['PU1_mRNA_cyto']], 0)
    G1prot_c    = max(y[IDX['GATA1_Protein_cyto']], 0)
    P1prot_c    = max(y[IDX['PU1_Protein_cyto']], 0)
    G1          = max(y[IDX['GATA1_Protein_nuc']], 0)
    P1          = max(y[IDX['PU1_Protein_nuc']], 0)
    pG1         = max(y[IDX['pGATA1_nuc']], 0)
    pP1         = max(y[IDX['pPU1_nuc']], 0)
    G1gene      = max(y[IDX['GATA1_Gene']], 1.0)   # genes are constant sources
    P1gene      = max(y[IDX['PU1_Gene']], 1.0)

    # Energy (buffered — treat as constant)
    ATP = ATP0; ADP = ADP0; GTP = GTP0; GDP = GDP0; Pi = Pi0

    # Temperature-dependent Arrhenius factors
    A_trans  = RU(-7215.0 * (1/T - 1/310.15))   # transcription
    A_export = RU(-7215.0 * (1/T - 1/310.15))   # mRNA export (same Ea)
    A_transl = RU(-4810.0 * (1/T - 1/310.15))   # translation
    A_nimport= RU(-6012.0 * (1/T - 1/310.15))   # nuclear import
    A_deg    = RU(-6012.0 * (1/T - 1/310.15))   # all degradations
    A_energy = RU(-3608.0 * (1/T - 1/310.15))   # ATP/GTP synthesis

    # pH-dependent terms
    PU1_thresh_nuc  = 1.0 * 10**(0.5 * (pH_nuc  - 7.5))   # = 1.0 at pH 7.5
    GATA1_thresh_nuc = 1.0 * 10**(0.5 * (pH_nuc - 7.5))
    MgATP = ATP * Mg_cyto / (0.06 + Mg_cyto)

    # ── Transition rates (from model JSON) ────────────────────────────────────
    # Receptor binding/unbinding
    r_EPO_bind     = 0.01   * EPO   * EPOR_f
    r_EPO_unbind   = 0.0001 * EPOR_b
    r_GCSF_bind    = 0.01   * GCSF  * GCSFR_f
    r_GCSF_unbind  = 0.0006 * GCSFR_b
    r_EPOR_intern  = 0.1    * EPOR_b
    r_GCSFR_intern = 0.1    * GCSFR_b
    r_EPOR_recycle = 0.1    * EPOR_i
    r_GCSFR_recycle= 0.1    * GCSFR_i

    # Transcription (FB1/FB2 autoactivation + cross-inhibition + cytokine boost)
    pH_G1_inh = (P1 / GATA1_thresh_nuc)**2
    pH_P1_inh = (G1 / PU1_thresh_nuc)**2
    r_G1_trans = (0.08
                  * (1 + 0.5 * G1 / (5 + G1))
                  / (1 + pH_G1_inh)
                  * (1 + 2 * EPOR_b / (5 + EPOR_b))
                  * A_trans)
    r_P1_trans = (0.08
                  * (1 + 0.5 * P1 / (5 + P1))
                  / (1 + pH_P1_inh)
                  * (1 + 2 * GCSFR_b / (5 + GCSFR_b))
                  * A_trans)

    # mRNA export (nuclear → cytoplasmic)
    r_G1mRNA_exp = 0.1 * G1mRNA_n * GTP / (50 + GTP) * RU(-((pH_nuc - 7.5)**2) / 0.5) * A_export
    r_P1mRNA_exp = 0.1 * P1mRNA_n * GTP / (50 + GTP) * RU(-((pH_nuc - 7.5)**2) / 0.5) * A_export

    # Translation
    r_G1_transl = 0.2 * G1mRNA_c * MgATP / (100 + MgATP) * GTP / (10 + GTP) * (ATP + 0.5*ADP) / (ATP + ADP + 0.01) * A_transl
    r_P1_transl = 0.2 * P1mRNA_c * MgATP / (100 + MgATP) * GTP / (10 + GTP) * (ATP + 0.5*ADP) / (ATP + ADP + 0.01) * A_transl

    # Nuclear import
    r_G1_nimport = 0.05 * G1prot_c * GTP / (50 + GTP) * RU(-((pH_cyto - 7.4)**2) / 0.5) * A_nimport
    r_P1_nimport = 0.05 * P1prot_c * GTP / (50 + GTP) * RU(-((pH_cyto - 7.4)**2) / 0.5) * A_nimport

    # mRNA degradation
    r_G1mRNA_ndeg = 0.005 * G1mRNA_n * A_deg
    r_G1mRNA_cdeg = 0.1   * G1mRNA_c * A_deg
    r_P1mRNA_ndeg = 0.005 * P1mRNA_n * A_deg
    r_P1mRNA_cdeg = 0.1   * P1mRNA_c * A_deg

    # Protein cytoplasmic degradation
    r_G1prot_cdeg = 0.075 * G1prot_c * A_deg
    r_P1prot_cdeg = 0.075 * P1prot_c * A_deg

    # Protein nuclear degradation (EPO/GCSF-dependent protection)
    r_G1prot_ndeg = 0.05 * (1 + 2 * (1 - EPOR_b  / (0.5 + EPOR_b ))) * G1 * A_deg
    r_P1prot_ndeg = 0.05 * (1 + 2 * (1 - GCSFR_b / (0.5 + GCSFR_b))) * P1 * A_deg

    # Phosphorylation/ubiquitination (FB3/FB4 cross-suppression)
    r_G1_phospho   = 0.05   * EPOR_b  / (2 + EPOR_b)  * G1  * ATP / (2000 + ATP)
    r_pG1_deg      = 0.015  * pG1 * A_deg
    r_pG1_ub_deg   = 0.1333 * pG1 / (3 + pG1) * P1 * ATP / (2000 + ATP)   # FB3: pG1 degraded by P1
    r_P1_phospho   = 0.05   * GCSFR_b / (2 + GCSFR_b) * P1  * ATP / (2000 + ATP)
    r_pP1_deg      = 0.015  * pP1 * A_deg
    r_pP1_ub_deg   = 0.1333 * pP1 / (3 + pP1) * G1 * ATP / (2000 + ATP)   # FB4: pP1 degraded by G1

    # ── Stoichiometry → ODEs ──────────────────────────────────────────────────
    dy = np.zeros(N)

    # EPO_external: consumed by binding? — treated as chemostat (constant external)
    dy[IDX['EPO_external']]       = 0.0
    dy[IDX['GCSF_external']]      = 0.0

    # EPOR
    dy[IDX['EPOR_free']]          = -r_EPO_bind + r_EPO_unbind + r_EPOR_recycle
    dy[IDX['EPOR_bound']]         =  r_EPO_bind - r_EPO_unbind - r_EPOR_intern
    dy[IDX['EPOR_internalized']]  =  r_EPOR_intern - r_EPOR_recycle

    # GCSFR
    dy[IDX['GCSFR_free']]         = -r_GCSF_bind + r_GCSF_unbind + r_GCSFR_recycle
    dy[IDX['GCSFR_bound']]        =  r_GCSF_bind - r_GCSF_unbind - r_GCSFR_intern
    dy[IDX['GCSFR_internalized']] =  r_GCSFR_intern - r_GCSFR_recycle

    # mRNA nuclear
    dy[IDX['GATA1_mRNA_nuc']]     =  r_G1_trans   - r_G1mRNA_exp - r_G1mRNA_ndeg
    dy[IDX['PU1_mRNA_nuc']]       =  r_P1_trans   - r_P1mRNA_exp - r_P1mRNA_ndeg

    # mRNA cytoplasmic
    dy[IDX['GATA1_mRNA_cyto']]    =  r_G1mRNA_exp - r_G1_transl - r_G1mRNA_cdeg
    dy[IDX['PU1_mRNA_cyto']]      =  r_P1mRNA_exp - r_P1_transl - r_P1mRNA_cdeg

    # Protein cytoplasmic
    dy[IDX['GATA1_Protein_cyto']] =  r_G1_transl   - r_G1_nimport - r_G1prot_cdeg
    dy[IDX['PU1_Protein_cyto']]   =  r_P1_transl   - r_P1_nimport - r_P1prot_cdeg

    # Protein nuclear (key bistable variables)
    dy[IDX['GATA1_Protein_nuc']]  =  r_G1_nimport  - r_G1prot_ndeg - r_G1_phospho
    dy[IDX['PU1_Protein_nuc']]    =  r_P1_nimport  - r_P1prot_ndeg - r_P1_phospho

    # Phosphorylated forms
    dy[IDX['pGATA1_nuc']]         =  r_G1_phospho  - r_pG1_deg - r_pG1_ub_deg
    dy[IDX['pPU1_nuc']]           =  r_P1_phospho  - r_pP1_deg - r_pP1_ub_deg

    # Genes: constant
    dy[IDX['GATA1_Gene']]         = 0.0
    dy[IDX['PU1_Gene']]           = 0.0

    return dy


def run_ode(epo, gcsf=0.001, t_end=100000, g1_ic=1.0, p1_ic=1.0):
    """Run ODE to steady state. Returns final state dict."""
    y0 = make_ics(EPO_external=epo, GCSF_external=gcsf,
                  GATA1_Protein_nuc=g1_ic, PU1_Protein_nuc=p1_ic)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        sol = solve_ivp(odes, [0, t_end], y0, method='Radau',
                        rtol=1e-8, atol=1e-10, dense_output=False,
                        max_step=t_end/100)
    yf = sol.y[:, -1]
    return {k: yf[v] for k, v in IDX.items()}, sol.success


def run_ode_parametric(epo, gcsf=0.001, t_end=100000,
                       g1_ic=1.0, p1_ic=1.0,
                       km_auto=5.0, km_inhib=1.0, km_fb=3.0):
    """Run ODE with overridden Km parameters (for Option C sweep)."""
    y0 = make_ics(EPO_external=epo, GCSF_external=gcsf,
                  GATA1_Protein_nuc=g1_ic, PU1_Protein_nuc=p1_ic)

    def odes_param(t, y):
        # identical to odes() but with parametric Km
        EPO         = max(y[IDX['EPO_external']], 0)
        GCSF        = max(y[IDX['GCSF_external']], 0)
        EPOR_f      = max(y[IDX['EPOR_free']], 0)
        EPOR_b      = max(y[IDX['EPOR_bound']], 0)
        EPOR_i      = max(y[IDX['EPOR_internalized']], 0)
        GCSFR_f     = max(y[IDX['GCSFR_free']], 0)
        GCSFR_b     = max(y[IDX['GCSFR_bound']], 0)
        GCSFR_i     = max(y[IDX['GCSFR_internalized']], 0)
        G1mRNA_n    = max(y[IDX['GATA1_mRNA_nuc']], 0)
        P1mRNA_n    = max(y[IDX['PU1_mRNA_nuc']], 0)
        G1mRNA_c    = max(y[IDX['GATA1_mRNA_cyto']], 0)
        P1mRNA_c    = max(y[IDX['PU1_mRNA_cyto']], 0)
        G1prot_c    = max(y[IDX['GATA1_Protein_cyto']], 0)
        P1prot_c    = max(y[IDX['PU1_Protein_cyto']], 0)
        G1          = max(y[IDX['GATA1_Protein_nuc']], 0)
        P1          = max(y[IDX['PU1_Protein_nuc']], 0)
        pG1         = max(y[IDX['pGATA1_nuc']], 0)
        pP1         = max(y[IDX['pPU1_nuc']], 0)

        ATP = ATP0; ADP = ADP0; GTP = GTP0; GDP = GDP0; Pi = Pi0

        A_trans   = RU(-7215.0 * (1/T - 1/310.15))
        A_export  = A_trans
        A_transl  = RU(-4810.0 * (1/T - 1/310.15))
        A_nimport = RU(-6012.0 * (1/T - 1/310.15))
        A_deg     = A_nimport
        MgATP = ATP * Mg_cyto / (0.06 + Mg_cyto)

        # Parametric Km values used here
        r_EPO_bind      = 0.01   * EPO   * EPOR_f
        r_EPO_unbind    = 0.0001 * EPOR_b
        r_GCSF_bind     = 0.01   * GCSF  * GCSFR_f
        r_GCSF_unbind   = 0.0006 * GCSFR_b
        r_EPOR_intern   = 0.1    * EPOR_b
        r_GCSFR_intern  = 0.1    * GCSFR_b
        r_EPOR_recycle  = 0.1    * EPOR_i
        r_GCSFR_recycle = 0.1    * GCSFR_i

        pH_G1_inh = (P1 / km_inhib)**2
        pH_P1_inh = (G1 / km_inhib)**2
        r_G1_trans = (0.08
                      * (1 + 0.5 * G1 / (km_auto + G1))
                      / (1 + pH_G1_inh)
                      * (1 + 2 * EPOR_b / (5 + EPOR_b))
                      * A_trans)
        r_P1_trans = (0.08
                      * (1 + 0.5 * P1 / (km_auto + P1))
                      / (1 + pH_P1_inh)
                      * (1 + 2 * GCSFR_b / (5 + GCSFR_b))
                      * A_trans)

        r_G1mRNA_exp = 0.1 * G1mRNA_n * GTP / (50 + GTP) * RU(-((pH_nuc - 7.5)**2) / 0.5) * A_export
        r_P1mRNA_exp = 0.1 * P1mRNA_n * GTP / (50 + GTP) * RU(-((pH_nuc - 7.5)**2) / 0.5) * A_export
        r_G1_transl  = 0.2 * G1mRNA_c * MgATP / (100 + MgATP) * GTP / (10 + GTP) * (ATP + 0.5*ADP) / (ATP + ADP + 0.01) * A_transl
        r_P1_transl  = 0.2 * P1mRNA_c * MgATP / (100 + MgATP) * GTP / (10 + GTP) * (ATP + 0.5*ADP) / (ATP + ADP + 0.01) * A_transl
        r_G1_nimport = 0.05 * G1prot_c * GTP / (50 + GTP) * RU(-((pH_cyto - 7.4)**2) / 0.5) * A_nimport
        r_P1_nimport = 0.05 * P1prot_c * GTP / (50 + GTP) * RU(-((pH_cyto - 7.4)**2) / 0.5) * A_nimport

        r_G1mRNA_ndeg = 0.005 * G1mRNA_n * A_deg
        r_G1mRNA_cdeg = 0.1   * G1mRNA_c * A_deg
        r_P1mRNA_ndeg = 0.005 * P1mRNA_n * A_deg
        r_P1mRNA_cdeg = 0.1   * P1mRNA_c * A_deg
        r_G1prot_cdeg = 0.075 * G1prot_c * A_deg
        r_P1prot_cdeg = 0.075 * P1prot_c * A_deg
        r_G1prot_ndeg = 0.05 * (1 + 2 * (1 - EPOR_b  / (0.5 + EPOR_b ))) * G1 * A_deg
        r_P1prot_ndeg = 0.05 * (1 + 2 * (1 - GCSFR_b / (0.5 + GCSFR_b))) * P1 * A_deg

        r_G1_phospho = 0.05   * EPOR_b  / (2 + EPOR_b)  * G1  * ATP / (2000 + ATP)
        r_pG1_deg    = 0.015  * pG1 * A_deg
        r_pG1_ub_deg = 0.1333 * pG1 / (km_fb + pG1) * P1 * ATP / (2000 + ATP)
        r_P1_phospho = 0.05   * GCSFR_b / (2 + GCSFR_b) * P1  * ATP / (2000 + ATP)
        r_pP1_deg    = 0.015  * pP1 * A_deg
        r_pP1_ub_deg = 0.1333 * pP1 / (km_fb + pP1) * G1 * ATP / (2000 + ATP)

        dy = np.zeros(N)
        dy[IDX['EPO_external']]       = 0.0
        dy[IDX['GCSF_external']]      = 0.0
        dy[IDX['EPOR_free']]          = -r_EPO_bind + r_EPO_unbind + r_EPOR_recycle
        dy[IDX['EPOR_bound']]         =  r_EPO_bind - r_EPO_unbind - r_EPOR_intern
        dy[IDX['EPOR_internalized']]  =  r_EPOR_intern - r_EPOR_recycle
        dy[IDX['GCSFR_free']]         = -r_GCSF_bind + r_GCSF_unbind + r_GCSFR_recycle
        dy[IDX['GCSFR_bound']]        =  r_GCSF_bind - r_GCSF_unbind - r_GCSFR_intern
        dy[IDX['GCSFR_internalized']] =  r_GCSFR_intern - r_GCSFR_recycle
        dy[IDX['GATA1_mRNA_nuc']]     =  r_G1_trans   - r_G1mRNA_exp - r_G1mRNA_ndeg
        dy[IDX['PU1_mRNA_nuc']]       =  r_P1_trans   - r_P1mRNA_exp - r_P1mRNA_ndeg
        dy[IDX['GATA1_mRNA_cyto']]    =  r_G1mRNA_exp - r_G1_transl  - r_G1mRNA_cdeg
        dy[IDX['PU1_mRNA_cyto']]      =  r_P1mRNA_exp - r_P1_transl  - r_P1mRNA_cdeg
        dy[IDX['GATA1_Protein_cyto']] =  r_G1_transl  - r_G1_nimport - r_G1prot_cdeg
        dy[IDX['PU1_Protein_cyto']]   =  r_P1_transl  - r_P1_nimport - r_P1prot_cdeg
        dy[IDX['GATA1_Protein_nuc']]  =  r_G1_nimport - r_G1prot_ndeg - r_G1_phospho
        dy[IDX['PU1_Protein_nuc']]    =  r_P1_nimport - r_P1prot_ndeg - r_P1_phospho
        dy[IDX['pGATA1_nuc']]         =  r_G1_phospho - r_pG1_deg - r_pG1_ub_deg
        dy[IDX['pPU1_nuc']]           =  r_P1_phospho - r_pP1_deg - r_pP1_ub_deg
        dy[IDX['GATA1_Gene']]         = 0.0
        dy[IDX['PU1_Gene']]           = 0.0
        return dy

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        sol = solve_ivp(odes_param, [0, t_end], y0, method='Radau',
                        rtol=1e-8, atol=1e-10, dense_output=False,
                        max_step=t_end/100)
    yf = sol.y[:, -1]
    return {k: yf[v] for k, v in IDX.items()}, sol.success


def two_ic_spread(epo, gcsf=0.001, **km_kwargs):
    """Return (ery_ratio, sym_ratio, mye_ratio) for a given EPO and Km set."""
    results = {}
    for label, g1, p1 in [('ERY', 5.0, 0.2), ('SYM', 1.0, 1.0), ('MYE', 0.2, 5.0)]:
        s, _ = run_ode_parametric(epo, gcsf=gcsf, g1_ic=g1, p1_ic=p1, **km_kwargs)
        results[label] = s['GATA1_Protein_nuc'] / max(s['PU1_Protein_nuc'], 1e-12)
    return results


if __name__ == '__main__':
    # ── Option C Km sweep: find minimal change that restores bistability ──────
    print('Option C — Km sweep to find bistability boundary')
    print('EPO=1.0 µM, GCSF=0.001 mM, symmetric 1×ICs')
    print('Bistability = ERY-start and MYE-start converge to DIFFERENT steady states')
    print()

    # Grid: km_auto × km_inhib; keep km_fb proportional (= 2×km_auto)
    km_auto_values  = [5.0, 1.0, 0.5, 0.2, 0.15, 0.10, 0.08, 0.05]
    km_inhib_values = [1.0, 0.5, 0.2, 0.15, 0.10, 0.08, 0.05]

    # Use GCSF=1.0 (same units as EPO) so GCSFR is active and can sustain MYE attractor.
    # At GCSF=0.001 there is no MYE cytokine signal → trivially monostable ERY.
    gcsf_balanced = 1.0
    print(f'  (EPO=1.0, GCSF={gcsf_balanced} — balanced cytokines)')
    print(f'{"km_auto":>8}  {"km_inhib":>9}  {"km_fb":>6}  {"ERY_r":>7}  {"SYM_r":>7}  {"MYE_r":>7}  {"spread":>7}  {"bistable?":>10}')
    print('-' * 80)
    for km_a in km_auto_values:
        for km_i in km_inhib_values:
            km_f = 2 * km_a
            res = two_ic_spread(1.0, gcsf=gcsf_balanced, km_auto=km_a, km_inhib=km_i, km_fb=km_f)
            spread = res['ERY'] - res['MYE']
            bistable = spread > 0.5
            flag = ' <<<' if bistable else ''
            print(f'{km_a:>8.3f}  {km_i:>9.3f}  {km_f:>6.3f}  '
                  f'{res["ERY"]:>7.3f}  {res["SYM"]:>7.3f}  {res["MYE"]:>7.3f}  '
                  f'{spread:>7.3f}  {"YES" if bistable else "no":>10}{flag}')

    # ── For any bistable Km set, sweep EPO/GCSF to map the bifurcation ──────
    print()
    print('EPO sweep with GCSF=1.0 (balanced), looking for bistable window')
    candidates = [
        dict(km_auto=5.00, km_inhib=1.00, km_fb=10.0),   # v4 original (baseline)
        dict(km_auto=0.50, km_inhib=0.20, km_fb=1.00),
        dict(km_auto=0.20, km_inhib=0.10, km_fb=0.40),
        dict(km_auto=0.10, km_inhib=0.05, km_fb=0.20),
    ]
    epo_sweep = [0.01, 0.1, 0.3, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 50.0]
    for cand in candidates:
        km_a = cand['km_auto']; km_i = cand['km_inhib']
        print(f'\n  km_auto={km_a}, km_inhib={km_i}, km_fb={cand["km_fb"]}')
        print(f'  {"EPO":>7}  {"ERY_r":>7}  {"SYM_r":>7}  {"MYE_r":>7}  {"spread":>7}  {"bistable?":>10}')
        any_bistable = False
        for epo in epo_sweep:
            res = two_ic_spread(epo, gcsf=gcsf_balanced, **cand)
            spread = res['ERY'] - res['MYE']
            bistable = spread > 0.5
            any_bistable = any_bistable or bistable
            flag = ' <<<' if bistable else ''
            print(f'  {epo:>7.3f}  {res["ERY"]:>7.3f}  {res["SYM"]:>7.3f}  {res["MYE"]:>7.3f}  '
                  f'{spread:>7.3f}  {"YES" if bistable else "no":>10}{flag}')
        if not any_bistable:
            print('  (no bistability at any EPO)')
    print()
