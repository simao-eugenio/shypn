# Manuscript Figures

## Figure 1: Basin of Attraction - B. subtilis Sporulation
**File:** `bacillus_basin_of_attraction.pdf`
- **Type:** State space analysis
- **Content:** Basin of attraction showing commitment regions for sporulation vs competence pathways
- **Source:** Thermodynamics project, validated model
- **Placement:** Section 6.2 (Case Study 2: B. subtilis Sporulation)

## Figure 2: Hierarchical Decision Cascade
**File:** `decision_cascade.pdf`
- **Type:** Temporal layer activation
- **Content:** 5-layer hierarchy showing sequential activation (Spo0A~P → SigmaH → Septum → SigmaF → SigmaE)
- **Panels:** 2 (Normal conditions vs Stress conditions)
- **Source:** Generated from thermodynamics/scripts/plot_decision_cascade.py
- **Placement:** Section 6.2 (Case Study 2: B. subtilis Sporulation)

## Usage in LaTeX

```latex
\begin{figure}[h]
\centering
\includegraphics[width=\columnwidth]{figures/bacillus_basin_of_attraction.pdf}
\caption{Basin of attraction analysis for \textit{B. subtilis} sporulation...}
\label{fig:basin_attraction}
\end{figure}

\begin{figure}[h]
\centering
\includegraphics[width=\columnwidth]{figures/decision_cascade.pdf}
\caption{Hierarchical decision cascade showing layer preemption...}
\label{fig:decision_cascade}
\end{figure}
```
