"""
Check what SBML features might be hidden in the UI.

This script analyzes what we extract from SBML but might not visualize.
"""

print("=" * 80)
print("SBML FEATURES ANALYSIS - What's Extracted vs Visualized")
print("=" * 80)

features = [
    {
        "name": "Species",
        "extracted": "✅ Yes (SpeciesExtractor)",
        "visualized": "✅ Yes (circles/places)",
        "hidden_info": [
            "- annotation (ChEBI, KEGG, database IDs)",
            "- sbo_term (Systems Biology Ontology)",
            "- formula (chemical formula like C6H12O6)",
            "- charge (electrical charge)",
            "- substance_units",
            "- has_only_substance_units flag"
        ]
    },
    {
        "name": "Reactions", 
        "extracted": "✅ Yes (ReactionExtractor)",
        "visualized": "✅ Yes (rectangles/transitions)",
        "hidden_info": [
            "- annotation (database cross-references)",
            "- sbo_term",
            "- modifiers (shown as test arcs, but not labeled clearly)"
        ]
    },
    {
        "name": "Global Parameters",
        "extracted": "✅ Yes (ParameterExtractor)",
        "visualized": "⚠️  NOW VISIBLE as hexagons (just added)",
        "hidden_info": [
            "- Only shown if used in formulas",
            "- Unused global parameters still hidden"
        ]
    },
    {
        "name": "Local Parameters (in reactions)",
        "extracted": "✅ Yes (ReactionExtractor)",
        "visualized": "⚠️  NOW VISIBLE as hexagons (just added)",
        "hidden_info": [
            "- Km, Vmax, Ki, kcat values",
            "- Each reaction can have different parameter sets"
        ]
    },
    {
        "name": "Compartments",
        "extracted": "✅ Yes (CompartmentExtractor)",
        "visualized": "⚠️  NOW VISIBLE as hexagons if used in formulas",
        "hidden_info": [
            "- spatial_dimensions (usually 3)",
            "- units (volume units)",
            "- constant flag"
        ]
    },
    {
        "name": "Events",
        "extracted": "✅ Yes (EventExtractor)",
        "visualized": "❌ NO - Completely hidden!",
        "hidden_info": [
            "- trigger conditions (t > 100, [Glucose] < 0.1)",
            "- assignments (change species/parameters at trigger time)",
            "- delay (time delay before execution)",
            "- priority (for simultaneous events)",
            "- USE CASE: Drug addition, nutrient depletion, temperature changes"
        ]
    },
    {
        "name": "Unit Definitions",
        "extracted": "✅ Yes (UnitExtractor)",
        "visualized": "❌ NO - Hidden!",
        "hidden_info": [
            "- Custom units (mM, per_second, etc.)",
            "- SI conversion factors",
            "- Used for proper unit normalization"
        ]
    },
    {
        "name": "Annotations (MIRIAM)",
        "extracted": "✅ Yes (AnnotationExtractor)",
        "visualized": "❌ NO - Hidden!",
        "hidden_info": [
            "- Database cross-references (ChEBI, KEGG, UniProt)",
            "- identifiers.org URIs",
            "- SBO terms (Systems Biology Ontology)",
            "- Notes (free text)"
        ]
    },
    {
        "name": "Modifiers (catalysts/enzymes)",
        "extracted": "✅ Yes (ReactionExtractor)",
        "visualized": "⚠️  Partially (as test arcs, but not clearly labeled)",
        "hidden_info": [
            "- Shown as test arcs (dotted lines)",
            "- But no indication if it's a catalyst, inhibitor, or activator",
            "- SBO term would clarify role (extracted but not shown)"
        ]
    },
    {
        "name": "Stoichiometry",
        "extracted": "✅ Yes (ReactionExtractor)",
        "visualized": "✅ Yes (arc weights)",
        "hidden_info": []
    },
    {
        "name": "Initial Assignments",
        "extracted": "❌ NO - Not extracted!",
        "visualized": "❌ NO",
        "hidden_info": [
            "- SBML feature: set initial values using formulas",
            "- Example: S1_initial = S2 * 2.0",
            "- Used for computed initial conditions"
        ]
    },
    {
        "name": "Algebraic Rules",
        "extracted": "❌ NO - Not extracted!",
        "visualized": "❌ NO",
        "hidden_info": [
            "- SBML feature: algebraic constraints (0 = ...)",
            "- Example: 0 = ATP + ADP - TotalAdenylate",
            "- Used for conservation laws, steady-state assumptions"
        ]
    },
    {
        "name": "Assignment Rules",
        "extracted": "❌ NO - Not extracted!",
        "visualized": "❌ NO",
        "hidden_info": [
            "- SBML feature: computed variables (x = ...)",
            "- Example: TotalAdenylate = ATP + ADP + AMP",
            "- Updated continuously during simulation"
        ]
    },
    {
        "name": "Rate Rules",
        "extracted": "❌ NO - Not extracted!",
        "visualized": "❌ NO",
        "hidden_info": [
            "- SBML feature: differential equations (dx/dt = ...)",
            "- Example: dTemperature/dt = -k * (Temperature - T_ambient)",
            "- Used for continuous environmental changes"
        ]
    },
    {
        "name": "Function Definitions",
        "extracted": "❌ NO - Not extracted!",
        "visualized": "❌ NO",
        "hidden_info": [
            "- SBML feature: reusable functions",
            "- Example: MM(S, Km, Vmax) = Vmax * S / (Km + S)",
            "- Used to avoid formula duplication"
        ]
    },
    {
        "name": "Constraints",
        "extracted": "❌ NO - Not extracted!",
        "visualized": "❌ NO",
        "hidden_info": [
            "- SBML feature: validation constraints",
            "- Example: ATP > 0 (must always hold)",
            "- Used for model validation"
        ]
    }
]

print("\n")
for feature in features:
    print(f"\n{'=' * 80}")
    print(f"FEATURE: {feature['name']}")
    print(f"{'=' * 80}")
    print(f"Extracted: {feature['extracted']}")
    print(f"Visualized: {feature['visualized']}")
    if feature['hidden_info']:
        print(f"\nHidden Information:")
        for info in feature['hidden_info']:
            print(f"  {info}")

print("\n" + "=" * 80)
print("SUMMARY: BIGGEST GAPS")
print("=" * 80)
print("""
1. ❌ EVENTS - Fully extracted but completely hidden!
   - Critical for experimental protocols (drug addition, perturbations)
   - Should show as special visual elements (event markers on timeline?)
   
2. ❌ RULES (Assignment/Rate/Algebraic) - Not extracted at all!
   - Assignment rules: Computed variables
   - Rate rules: Continuous ODEs for environment
   - Algebraic rules: Conservation laws
   - Need RuleExtractor class
   
3. ❌ FUNCTION DEFINITIONS - Not extracted!
   - Reusable kinetic functions
   - Need FunctionExtractor class
   
4. ❌ INITIAL ASSIGNMENTS - Not extracted!
   - Computed initial conditions
   - Need InitialAssignmentExtractor class
   
5. ⚠️  ANNOTATIONS - Extracted but not shown!
   - Database IDs (ChEBI, KEGG) very useful for user
   - Should show in place/transition properties panel
   
6. ⚠️  SBO TERMS - Extracted but not shown!
   - Would clarify roles (catalyst vs inhibitor)
   - Should show as labels or tooltips
   
7. ⚠️  UNIT DEFINITIONS - Extracted but not visible!
   - Important for understanding parameter scales
   - Should show in properties panel

RECOMMENDATION:
- Parameters/Compartments: ✅ FIXED (now showing as hexagons)
- Events: HIGH PRIORITY - Need visual representation
- Rules: MEDIUM PRIORITY - Need extraction + visualization  
- Annotations/SBO: LOW PRIORITY - Show in properties panel
""")
