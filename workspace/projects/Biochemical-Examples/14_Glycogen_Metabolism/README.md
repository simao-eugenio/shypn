# Example 14: Glycogen Metabolism

## Overview

This model demonstrates **glycogen metabolism** - the synthesis and breakdown of glycogen, the primary glucose storage polysaccharide in animals. The model includes hormonal regulation (insulin promotes synthesis, glucagon/epinephrine promote breakdown) and allosteric regulation by metabolites.

## Biological Context

### Glycogen Structure
- Branched glucose polymer (α-1,4 and α-1,6 glycosidic bonds)
- Stored primarily in liver (~100g) and muscle (~400g)
- Provides rapid glucose mobilization during fasting or exercise
- Hepatic glycogen maintains blood glucose (4-6 mM)
- Muscle glycogen fuels local ATP production

### Metabolic Roles

**Liver Glycogen** (glucose homeostasis):
- Synthesis after meals (insulin signaling)
- Breakdown during fasting (glucagon signaling)
- Releases glucose to blood for other tissues
- Buffer against hypoglycemia

**Muscle Glycogen** (energy reserve):
- Synthesis during rest (insulin signaling)
- Breakdown during exercise (epinephrine signaling)
- Glucose-6-P retained for local glycolysis
- No glucose-6-phosphatase → cannot release glucose

## Biochemical Pathways

### 1. Glycogenesis (Synthesis)

**G6P → G1P → UDP-glucose → Glycogen**

1. **Phosphoglucomutase (PGM)**: G6P ⇌ G1P
   - Reversible interconversion
   - Km(G6P) = 0.02 mM, Km(G1P) = 0.01 mM

2. **UDP-glucose pyrophosphorylase (UGP)**: G1P + UTP → UDP-glucose + PPi
   - Thermodynamically unfavorable (ΔG°' = 0)
   - Driven forward by PPi hydrolysis (ΔG°' = -33.5 kJ/mol)
   - Km(G1P) = 0.3 mM, Km(UTP) = 0.1 mM

3. **Inorganic pyrophosphatase (PPase)**: PPi → 2 Pi
   - Highly exergonic (ΔG°' = -33.5 kJ/mol)
   - Makes UDP-glucose synthesis irreversible
   - Ubiquitous enzyme ensuring biosynthesis completion

4. **Glycogen synthase (GS)**: UDP-glucose + Glycogen(n) → Glycogen(n+1) + UDP
   - Rate-limiting enzyme for glycogenesis
   - Adds glucose to non-reducing ends (α-1,4 bonds)
   - Regulated by phosphorylation (inactive when phosphorylated)
   - Allosterically activated by G6P
   - Km(UDP-glucose) = 0.3 mM

5. **Branching enzyme (BE)**: Creates α-1,6 branches
   - Transfers 6-7 glucose units to create branch points
   - Every 8-12 residues along chains
   - Increases glycogen solubility and synthesis/degradation rate

### 2. Glycogenolysis (Breakdown)

**Glycogen → G1P → G6P**

1. **Glycogen phosphorylase (GP)**: Glycogen(n) + Pi → Glycogen(n-1) + G1P
   - Rate-limiting enzyme for glycogenolysis
   - Cleaves α-1,4 bonds phosphorolytically
   - Stops 4 residues from branch points
   - Regulated by phosphorylation (active when phosphorylated)
   - Allosterically activated by AMP, inhibited by ATP/G6P
   - Km(Pi) = 5 mM

2. **Debranching enzyme (DBE)**: Removes α-1,6 branch points
   - Dual activity: transferase + glucosidase
   - Transfers 3 glucose units to main chain
   - Hydrolyzes α-1,6 bond → free glucose (~8% of total)

3. **Phosphoglucomutase (PGM)**: G1P ⇌ G6P
   - Same enzyme as glycogenesis
   - Bidirectional flux depending on substrate concentrations

### 3. Glucose-6-phosphatase (Liver Only)

**G6P → Glucose + Pi**

- Exclusively in liver (and kidney)
- Allows glucose release to blood
- Absent in muscle → G6P enters glycolysis
- Km(G6P) = 2 mM

## Regulatory Mechanisms

### Hormonal Regulation (Covalent Modification)

**Insulin** (fed state - promotes storage):
- Activates protein phosphatase 1 (PP1)
- PP1 dephosphorylates glycogen synthase → ACTIVE
- PP1 dephosphorylates glycogen phosphorylase → INACTIVE
- Net effect: synthesis ON, breakdown OFF

**Glucagon/Epinephrine** (fasted/stress state - mobilizes glucose):
- Activates PKA (protein kinase A) via cAMP
- PKA phosphorylates glycogen synthase → INACTIVE
- PKA phosphorylates phosphorylase kinase → ACTIVE
- Phosphorylase kinase phosphorylates glycogen phosphorylase → ACTIVE
- Net effect: synthesis OFF, breakdown ON

### Allosteric Regulation (Metabolite Sensing)

**Glycogen Synthase**:
- Activated by G6P (substrate availability signal)
- Even phosphorylated form partly active with G6P

**Glycogen Phosphorylase** (muscle):
- Activated by AMP (energy demand signal)
- Inhibited by ATP, G6P (energy sufficiency signals)
- Liver phosphorylase less sensitive to allosteric regulation

### Substrate Cycling

**Futile cycling** between synthesis and breakdown:
- Both pathways never 100% off
- Allows rapid flux changes
- ~1-2% of glucose turnover lost as heat
- Amplifies regulatory signals

## Model Components

### Places (18 total)

**Metabolites**:
1. Glucose (blood/extracellular)
2. G6P (glucose-6-phosphate)
3. G1P (glucose-1-phosphate)
4. UTP (uridine triphosphate)
5. UDP-glucose (activated glucose)
6. UDP (uridine diphosphate)
7. PPi (inorganic pyrophosphate)
8. Pi (inorganic phosphate)
9. Glycogen (glucose polymer)
10. ATP (energy currency)
11. ADP
12. AMP (energy sensor)

**Hormones/Signals**:
13. Insulin (anabolic signal)
14. Glucagon (catabolic signal)
15. cAMP (second messenger)

**Enzymes** (regulatory states):
16. GS_active (glycogen synthase)
17. GP_active (glycogen phosphorylase)
18. PKA_active (protein kinase A)

### Transitions (12 total)

**Glycogenesis**:
1. PGM_synthesis (G6P → G1P)
2. UGP (G1P + UTP → UDP-glucose + PPi)
3. PPase (PPi → 2Pi)
4. GS (UDP-glucose + Glycogen(n) → Glycogen(n+1) + UDP)
5. Branching (creates α-1,6 branches)

**Glycogenolysis**:
6. GP (Glycogen(n) + Pi → Glycogen(n-1) + G1P)
7. Debranching (removes α-1,6 branches)
8. PGM_breakdown (G1P → G6P)

**Glucose Release** (liver):
9. G6Pase (G6P → Glucose + Pi)

**Regulation**:
10. GS_phosphorylation (inactivation by PKA)
11. GP_phosphorylation (activation by PKA)
12. cAMP_production (glucagon → cAMP → PKA activation)

### Arcs (40+ total)

**Normal arcs**: Substrate consumption/product formation
**Inhibitor arcs**: Feedback regulation
- ATP ⊣ GP (energy sufficiency inhibits breakdown)
- G6P ⊣ GP (product inhibition)
- AMP ⊣ GS (energy deficit inhibits synthesis)
- Glycogen ⊣ GS (storage limit)

**Test arcs**: Catalytic/regulatory
- G6P → GS (allosteric activation)
- Insulin → GS activation
- Glucagon → GP activation

## Physiological States

### Fed State (Post-Meal)
- High blood glucose (8-10 mM)
- Insulin elevated
- GS active, GP inactive
- Net glycogen synthesis
- G6P → glycogen

### Fasted State (Between Meals)
- Normal blood glucose (4-6 mM)
- Glucagon elevated
- GS inactive, GP active
- Net glycogen breakdown
- Glycogen → glucose (liver) or G6P (muscle)

### Exercise State
- Epinephrine elevated
- Muscle glycogen breakdown
- G1P → G6P → pyruvate → ATP
- Lactate production if anaerobic

### Prolonged Fasting (>12 hours)
- Liver glycogen depleted (~90%)
- Muscle glycogen preserved
- Gluconeogenesis predominates
- Ketone body production begins

## Kinetic Parameters

### Enzyme Kinetics (Michaelis-Menten)

**Glycogen Synthase**:
- Vmax = 10 μM/s (basal), 50 μM/s (G6P-activated)
- Km(UDP-glucose) = 300 μM
- Ki(ATP) = 5000 μM (ATP inhibits when very high)

**Glycogen Phosphorylase**:
- Vmax = 20 μM/s (liver), 40 μM/s (muscle)
- Km(Pi) = 5000 μM
- Ka(AMP) = 100 μM (muscle, allosteric activation)
- Ki(ATP) = 2000 μM
- Ki(G6P) = 1000 μM

**Phosphoglucomutase**:
- Vmax_forward = 100 μM/s (G6P → G1P)
- Vmax_reverse = 100 μM/s (G1P → G6P)
- Km(G6P) = 20 μM
- Km(G1P) = 10 μM

**UDP-glucose pyrophosphorylase**:
- Vmax = 50 μM/s
- Km(G1P) = 300 μM
- Km(UTP) = 100 μM

**Glucose-6-phosphatase** (liver only):
- Vmax = 30 μM/s
- Km(G6P) = 2000 μM

### Time Constants

- Glycogen synthesis: τ ≈ 1-2 hours (full storage)
- Glycogen breakdown: τ ≈ 15-30 minutes (complete depletion)
- Hormonal response: τ ≈ 2-5 minutes (cAMP signaling)
- Enzyme phosphorylation: τ ≈ 30 seconds to 2 minutes

### Initial Conditions (Fed State)

**Metabolites** (1 token = 1 μM):
- Glucose: 5000 μM (5 mM blood glucose)
- G6P: 200 μM
- G1P: 20 μM
- UDP-glucose: 500 μM
- Glycogen: 50000 μM (50 mM glucose equivalents, ~8g in 100g liver)
- ATP: 5000 μM
- ADP: 1000 μM
- AMP: 50 μM
- UTP: 400 μM
- UDP: 100 μM
- Pi: 5000 μM
- PPi: 10 μM

**Regulatory**:
- Insulin: 100 μM (high)
- Glucagon: 10 μM (low)
- cAMP: 1 μM (basal)
- GS_active: 80% (mostly active)
- GP_active: 20% (mostly inactive)

## Learning Objectives

1. **Reciprocal regulation**: How insulin and glucagon have opposite effects
2. **Covalent modification cascades**: Amplification through phosphorylation
3. **Allosteric control**: Fine-tuning by metabolites (AMP, ATP, G6P)
4. **Substrate cycling**: Why both pathways are never completely off
5. **Tissue-specific metabolism**: Liver vs muscle glycogen functions
6. **Energy coupling**: Role of UTP → UDP and PPi hydrolysis
7. **Branching importance**: Surface area for rapid synthesis/degradation

## Clinical Relevance

**Glycogen Storage Diseases**:
- Type I (von Gierke): G6Pase deficiency → hypoglycemia
- Type II (Pompe): Lysosomal α-glucosidase deficiency
- Type V (McArdle): Muscle phosphorylase deficiency → exercise intolerance

**Diabetes**:
- Impaired glycogen synthesis (insulin resistance)
- Excessive hepatic glucose output (unrestrained glucagon)

**Hypoglycemia**:
- Insufficient glycogen stores (prolonged fasting)
- Excessive insulin (hyperinsulinemia)

## References

1. Berg JM, Tymoczko JL, Stryer L. *Biochemistry*, 8th ed. (2015) - Chapter 21
2. Nelson DL, Cox MM. *Lehninger Principles of Biochemistry*, 7th ed. (2017) - Chapter 15
3. Roach PJ et al. "Glycogen and its metabolism" *Biochem J* (2012) 441:763-787
4. Jensen J, Lai Y. "Regulation of muscle glycogen synthase phosphorylation" *Am J Physiol Endocrinol Metab* (2009)
