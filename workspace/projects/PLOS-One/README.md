# PLOS ONE Submission — Signal Hierarchy Theory for Biological Petri Nets

**Journal:** PLOS ONE  
**Submission ID:** PONE-D-26-05900  
**Status:** Revision under review

## Contents

```
PLOS-One/
├── models/
│   └── bacillus_sporulation_v9.shy        ← canonical B. subtilis paper model (v9)
├── sweep/
│   └── sweep_config_factorial.json        ← 25-condition factorial sweep (INITIAL_NUTRIENTS × LOADING_DOSE × SinR)
├── results/
│   ├── run_20260614_123652/               ← 25-condition factorial sweep output
│   │   ├── config.json                    ← full sweep parameters as executed
│   │   └── summary.csv                   ← per-condition summary statistics
│   └── run_20260617_173741/               ← NaturalPath single-condition run
│       ├── config.json
│       ├── summary.csv
│       ├── provenance.json                ← git SHA, model sha256, dispatch metadata
│       ├── model_snapshot.shy             ← exact model bytes used in this run
│       └── resource_usage.json
├── scripts/
│   ├── fig_topology_annotated.py          ← generates Fig 2 (network topology)
│   ├── fig_preemption_cascade.py          ← generates Fig 3 (preemption cascade)
│   └── fig_waddington_landscape.py        ← generates Fig 4 (Waddington landscape)
├── figures/
│   ├── bacillus_sporulation_v9_titled.pdf ← Fig 2
│   ├── fig_preemption_cascade_v3.pdf      ← Fig 3
│   └── fig_waddington_landscape.pdf       ← Fig 4
└── manuscript/
    ├── main_plos_one_revision.tex          ← revised manuscript (LaTeX source)
    ├── main_plos_one_SUBMITTED_ORIGINAL.tex ← frozen original submission baseline
    ├── references_plos_one.bib
    └── answers/
        ├── response_letter.tex
        └── cover_letter.tex
```

## Reproducing the sweep

Requires the SHyPN engine (this repository) and Python ≥ 3.10 with dependencies
installed (`pip install -e .` from repo root).

```bash
# Reproduce the 25-condition factorial sweep (Fig 3 / Fig 4 data source)
python -m shypn.cli.sweep \
    --project workspace/projects/PLOS-One \
    --sweep   workspace/projects/PLOS-One/sweep/sweep_config_factorial.json \
    --workers 4 --verbose
```

Output lands in `workspace/projects/PLOS-One/experiments/results/run_<timestamp>/`.

## Reproducing the figures

```bash
cd workspace/projects/PLOS-One/scripts

# Fig 2 — B. subtilis network topology
python fig_topology_annotated.py

# Fig 3 — Preemption cascade
python fig_preemption_cascade.py

# Fig 4 — Waddington landscape
python fig_waddington_landscape.py
```

## Model

`models/bacillus_sporulation_v9.shy` is a JSON-based Signal Hierarchical Petri Net
(SHPN) file for the *B. subtilis* sporulation commitment decision.
It encodes 40 places, 36 transitions, and 114 arcs.
Open with `python src/shypn.py` (SHyPN GUI).

## Experimental anchor

The sporulation efficiency data used for validation comes from:

> Fujita M, Losick R (2005). Evidence that entry into sporulation in *Bacillus
> subtilis* is governed by a gradual increase in the level and activity of the
> master regulator Spo0A. *Genes Dev.* 19:2236–2244. Fig. 2A–D.

Values used: ~52% efficiency (gradual KinA phosphorelay) vs. ~5% (abrupt Spo0A*
induction). No proprietary data were used.

## Citation

If you use this model or code, please cite:

```bibtex
@software{shypn2026,
  title   = {SHYpn: Signal Hierarchical Petri Nets for Systems Biology},
  author  = {Simão, Eugénio},
  year    = {2026},
  version = {2.6.1},
  doi     = {10.5281/zenodo.18749556},
  url     = {https://github.com/simao-eugenio/shypn}
}
```
