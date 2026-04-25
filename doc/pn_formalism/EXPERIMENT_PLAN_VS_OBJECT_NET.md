# Experiment Plan vs Object-Net — HPN architectural rule

**Status**: STRICT — applies to all `.shy` models and all sweep dispatches.
**Authority**: HPN formalism (Simão 2025, `manuscript/main_plos_one.tex`).
**Adopted**: 2026-04-25.

---

## 1. The two artifacts inside a `.shy` file

A `.shy` file bundles two architecturally separate things:

1. **Object-net** — the biology. Reusable across experiments. Its
   dynamics emerge **entirely from its own topology** (places,
   transitions, arcs, intrinsic Φ rate functions over its own places).
2. **Experiment plan** — parameter places + events. Run-specific.
   Encodes the protocol / intervention being studied.

The object-net is the *system under study*. The experiment plan is
*how we are poking it on this particular run*. They must remain
separable because the same biology is reused under many protocols.

---

## 2. Why the separation is formal, not stylistic

Per HPN (Simão 2025, §"Connected vs. Remote Information Access"), a
Bio-PN is two coupled graphs:

| Graph | Symbol | Role |
|---|---|---|
| Execution graph | $G_E = (P, T, F)$ | Mass-balanced biochemistry |
| Information graph | $G_s = (\Psi, F_s)$ | DAG of commitment, layered $\lambda$ |

Parameter places (`Disease_Severity`, `Age`, `Temperature`, `pH`,
`LOADING_DOSE`, `MAINT_DOSE`, …) belong to **neither** graph.
Putting them in either corrupts:

- $G_E$ — mass balance, stoichiometry analysis, conservation laws.
- $G_s$ — the layer function $\lambda$, the basin boundary
  $M_{\text{commit}} = \theta + W_s$, the `PreemptionCheck` cascade,
  and the acyclicity-theorem proof scope.

---

## 3. Sensing channels — what is and is not legal

The formalism admits **two** mechanisms by which a transition's rate
can depend on a place's marking:

1. **Connected channels ($F_s$, signal flow arcs)** — topology-explicit,
   consumptive, hierarchical (governed by `PreemptionCheck`), with
   basin floor $\theta$ for structural enablement.
2. **Remote sensing ($\Phi$, rate functions)** — equation-implicit,
   non-consumptive, **no hierarchy / no preemption / no $\theta$**.
   The rate function references $M(p_{\text{remote}})$ by name; no arc
   is required.

A place that appears **only inside a rate function** (no arcs of any
kind) is therefore formally legal — it is "remote sensing" per
Simão 2025. **It is not a metadata leak.** What it *is*, is a modelling
choice with weaker semantics: no hierarchical preemption.

> If the modeller wants `DSev = 0` to *structurally* disable a
> transition, they must add a signal-flow arc ($F_s$) with $\theta \ge 1$.
> Merely referencing `DSev` inside $\Phi$ is not enough.

---

## 4. Definitions — place vs parameter place

- **Place** (`p \in P`): a biological/physical reservoir of tokens. Has
  dynamics. Tokens flow in/out through arcs (or are added/removed by
  events). Other transitions consume/produce it as **mass-balanced
  state**. Participates in conservation analysis, signal hierarchy,
  reachability.
- **Parameter place** (UI flag `is_parameter_place=True`): a scalar
  modeller-chosen value with **no dynamics**. It only constrains the
  dynamics of true places via rate functions and event schedules. It
  belongs to the **environment / experiment-plan block**, not to the
  active topology.

### Test for distinguishing them

A symbol is a (true) place iff:

1. Tokens flow in/out of it through arcs **or** events `add` to it as a
   bolus during simulation, **and**
2. Other transitions consume/produce it as mass-balanced state.

If the symbol's marking is set once at $t=0$ (or only via event-schedule
overrides) and never changes through firings — it is a parameter, not
a place.

---

## 5. STRICT rules

### 5.1 Parameter places MUST NOT

- Appear by name in any **object-net** rate function (no remote
  sensing of them from biological transitions; even though $\Phi$ is
  DAG-neutral, this makes biology rates depend on experiment metadata
  and breaks reusability).
- Have $F$, $F_s$, or $F_t$ arcs to/from object-net transitions.
- Be listed in the `signal_places` of any object-net transition.
- Be referenced via the `is_environment_aware` backdoor or by
  hard-coded `Q10` / `Temperature` / `pH` / `Age` symbols inside rate
  function strings.

### 5.2 The ONLY legal bridge: events

Events read parameter-place values and apply **discrete interventions**
to biological places (set marking, add/remove tokens, fire at scheduled
times).

**Example (legal):**

```yaml
event: evt_install_disease
  trigger: t == 0
  action:
    Aβ_Monomer := DSev * 5.0
```

### 5.3 Visual marker

Parameter places render as a **rounded square**. This is the canvas
contract that says "this node is outside both $G_E$ and $G_s$".
See `src/shypn/netobjs/place.py::_draw_rounded_square_path`.

| Shape | Place kind | Graph membership |
|---|---|---|
| Circle ○ | Regular biological place | $P \setminus \Psi$ in $G_E$ |
| Hexagon ⬡ | Signal place ($\Psi$) | $\Psi \subseteq P$ in $G_E$ + node in $G_s$ |
| **Rounded square ▢** | **Parameter place** | **outside $G_E$ and $G_s$** |

### 5.4 No semantic mirroring (one concept ↔ one carrier)

A conceptual quantity (e.g. `Age`, `Temperature`, `pH`,
`Disease_Severity`) is represented by **exactly one** carrier. The
three legal carriers, mutually exclusive per concept, are:

1. **Pure parameter place ▢** — no arcs, never appears in any object-net
   rate function. Read by events only. Swept via the parameter
   mechanism.
2. **Signal place ⬡** — in $\Psi$, has at least one $F_s$ arc,
   participates in `PreemptionCheck` and the layered information
   hierarchy. May also be referenced inside $\Phi$.
3. **Remote-sensed regular place ○** — referenced by name inside one or
   more rate functions $\Phi$ (Simao 2025 "remote sensing"); has its
   own dynamics or is held constant by absence of producers/consumers.

**Forbidden:** two carriers for the same concept (e.g. a signal place
`Age` *and* a parameter place `Age_param` whose value is supposed to
shadow it). This produces two sources of truth, and the sweep ↔ model
superposition rule of §6 cannot resolve it because the override target
is ambiguous.

**Corollary — sweeping `initial_marking` of a topology-coupled place
is legal.** When `Age` is a signal place whose marking the biology
legitimately senses, sweeping `Age.initial_marking` is a standard
initial-condition perturbation of the model state $M_0$. It is **not**
a superposition violation — the place is the single carrier, and
$M_0(\text{Age})$ is one of its attributes. The sweep ensures each
dispatch starts from a different point of $M_0$, exactly as intended.

**The check:** if you find yourself wanting to add `X_param` so that
`X` (already in $\Psi$ or referenced in $\Phi$) is sweepable from the
UI, you don't need it — sweep `X.initial_marking` directly. Conversely,
if `X` has no arcs and is not referenced in any $\Phi$, it is not a
topology element; flag it `is_parameter_place=true` and remove the
signal/regular flag.

---

## 6. Sweep ↔ model superposition

When a sweep targets an experiment-planning object (parameter-place
value or event field), the **sweep value is canonical for that
dispatch** and the static value in the `.shy` file is **suppressed**.

### Forbidden

A parameter has both a static value AND a sweep value, silently
merged. Failure modes: silent shadow, silent merge, cross-product
explosion.

Also forbidden: a sweep targets `X.initial_marking` while a parameter
place `X_param` exists in the same model carrying the "same" concept.
This is the §5.4 mirroring smell surfacing at sweep time — fix the
model (collapse to one carrier), not the sweep config.

### Required

- Engine logs `[override] X = sweep_value (was static_value in model)`.
- Provenance records `parameter_sources: {X: "sweep" | "model_default"}`
  per condition.
- Validator emits a notice on redundant override (sweep value equals
  static default).
- The baseline cell is named `ModelDefaults` so it cannot be confused
  with a swept condition.

### Exception

Superposition is allowed **only** when it demonstrably reduces
simulation complexity (e.g. nested factorial sharing a fixed level).
It must be declared explicitly in the sweep config:

```json
"superposition_intent": "complexity_reduction"
```

The dispatcher confirms with a green-flag log line. Without explicit
declaration, superposition is treated as a configuration smell.

---

## 7. Diagnostic consequence

If the object-net does not exhibit a desired behaviour (e.g. a healthy
fixed point at `NH = 100` when initialised healthy with no events
firing), **the topology is wrong**. The fix is structural:

- add sinks
- add clearance arcs
- rebalance reactions
- add the missing $F_s$ arc with the right $\theta$ if the gating
  must be structural

**Never patch via parameter-place multipliers or rate-function
shortcuts.** Those only mask the topological gap and make the model
non-reusable.

---

## 8. Required v4 refactor pattern (when migrating an existing model)

1. Remove environment scalars from `places:` if they have no dynamics.
2. Move them to `metadata.parameters:` or `thermodynamic_settings:`
   (or flag the place as `is_parameter_place: true` to keep it visible
   on the canvas as a rounded square).
3. Rate functions of biological transitions must not reference them.
4. Sweep configs target the parameter directly (env-channel or
   parameter place), not a biological place's `initial_marking`.
5. Audit object-net for places with no consuming arcs (monotonically
   accumulating species) — add sinks until the healthy fixed point
   emerges from topology alone.
