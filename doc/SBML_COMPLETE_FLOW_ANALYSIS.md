# SBML Complete Flow Analysis: Fetch → Parse → Convert → Save

## Overview

This document traces the complete SBML import flow from loading an XML file through parsing, conversion, and saving as a .shy Petri net model.

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SBML IMPORT COMPLETE FLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

USER INPUT (2 modes)
├─ Mode 1: File Selection
│  └─ Browse button → FileChooser → Select .sbml/.xml file
│     → Sets: self.current_filepath
│
└─ Mode 2: BioModels Fetch
   └─ Enter ID (e.g., BIOMD0000000001) → Fetch button
      → Downloads XML from biomodels.org
      → Saves to: project/pathways/BIOMD0000000001.xml
      → Sets: self.current_filepath

═════════════════════════════════════════════════════════════════════════════
STAGE 1: PARSE SBML XML → PathwayData
═════════════════════════════════════════════════════════════════════════════

📍 Entry Point: _on_parse_clicked() or auto-triggered after fetch
📂 File: src/shypn/helpers/sbml_import_panel.py (line 814)

def _on_parse_clicked(self, button):
    filepath = self.current_filepath
    
    # Background thread
    def parse_thread():
        parsed_pathway = self.parser.parse_file(filepath)  # ← SBMLParser
        validation_result = self.validator.validate(parsed_pathway)
        GLib.idle_add(self._on_parse_complete, parsed_pathway, validation_result)

───────────────────────────────────────────────────────────────────────────────
PARSE: SBMLParser.parse_file()
📂 File: src/shypn/data/pathway/sbml_parser.py (line 371)

Input:  SBML XML file (e.g., BIOMD0000000001.xml)
Process:
  1. Read XML using python-libsbml
  2. Extract model components:
     • SpeciesExtractor → List[Species]
       - id, name, compartment, initial_concentration
     • ReactionExtractor → List[Reaction]
       - id, name, reactants[], products[], kinetic_law
     • CompartmentExtractor → Dict[str, str]
     • ParameterExtractor → Dict[str, float]
  3. Build PathwayData object

Output: PathwayData
  ├─ species: List[Species]
  │  └─ Species(id, name, compartment, initial_concentration)
  ├─ reactions: List[Reaction]
  │  ├─ reactants: [(species_id, stoichiometry), ...]
  │  ├─ products: [(species_id, stoichiometry), ...]
  │  └─ kinetic_law: KineticLaw(formula, parameters)
  ├─ compartments: Dict[id → name]
  ├─ parameters: Dict[name → value]
  └─ metadata: Dict (name, notes, organism)

Example Output:
  PathwayData:
    species = [
      Species(id="glucose", name="Glucose", initial_concentration=5.0),
      Species(id="g6p", name="G6P", initial_concentration=0.0),
      ...
    ]
    reactions = [
      Reaction(
        id="hexokinase",
        name="Hexokinase",
        reactants=[("glucose", 1), ("atp", 1)],
        products=[("g6p", 1), ("adp", 1)]
      ),
      ...
    ]

───────────────────────────────────────────────────────────────────────────────
VALIDATE: PathwayValidator.validate()
📂 File: src/shypn/data/pathway/pathway_validator.py

Checks:
  ✓ All species referenced in reactions exist
  ✓ All reactions have at least 1 reactant or product
  ✓ Stoichiometry values are positive
  ✓ Units are consistent

Output: ValidationResult(is_valid, errors[], warnings[])

───────────────────────────────────────────────────────────────────────────────
RESULT: _on_parse_complete()
📂 File: src/shypn/helpers/sbml_import_panel.py (line 864)

Store results:
  self.parsed_pathway = parsed_pathway
  self.validation_result = validation_result

Update UI:
  • Preview shows: name, # species, # reactions
  • Status shows: "✓ Parse complete"
  • Enable "Import to Canvas" button

If auto-continuing (BioModels flow):
  → Auto-trigger _on_load_clicked()

═════════════════════════════════════════════════════════════════════════════
STAGE 2: POST-PROCESS → ProcessedPathwayData
═════════════════════════════════════════════════════════════════════════════

📍 Entry Point: _on_load_clicked()
📂 File: src/shypn/helpers/sbml_import_panel.py (line 626)

def _on_load_clicked(self, button):
    parsed_pathway = self.parsed_pathway
    scale_factor = self.sbml_scale_spin.get_value()
    
    # Background thread
    def load_thread():
        # POST-PROCESS
        postprocessor = PathwayPostProcessor(scale_factor=scale_factor)
        processed = postprocessor.process(parsed_pathway)
        
        # CONVERT
        document_model = self.converter.convert(processed)
        
        # SAVE
        GLib.idle_add(self._on_load_and_save_complete, document_model, pathway_name)

───────────────────────────────────────────────────────────────────────────────
POST-PROCESS: PathwayPostProcessor.process()
📂 File: src/shypn/data/pathway/pathway_postprocessor.py

Input:  PathwayData (no positions, no colors)
Process:
  1. LAYOUT: Assign positions to species/reactions
     • Algorithm: Force-directed or hierarchical
     • Spacing: node_spacing * scale_factor
     • Result: positions Dict[id → (x, y)]
  
  2. COLORS: Assign colors by compartment
     • cytosol → light blue
     • nucleus → light green
     • Result: colors Dict[compartment → hex_color]
  
  3. TOKEN NORMALIZATION: concentration → tokens
     • Find min non-zero concentration
     • Divide all concentrations by min
     • Round to integers
     • Result: initial_tokens (int) for each species

Output: ProcessedPathwayData
  ├─ species: List[Species] (with initial_tokens added)
  ├─ reactions: List[Reaction]
  ├─ positions: Dict[species_id → (x, y)]
  ├─ colors: Dict[compartment → hex_color]
  ├─ compartments: Dict
  ├─ parameters: Dict
  └─ metadata: Dict

Example:
  ProcessedPathwayData:
    species[0].initial_tokens = 5  # glucose: 5.0 mM → 5 tokens
    positions = {
      "glucose": (100.0, 200.0),
      "g6p": (300.0, 200.0),
      ...
    }
    colors = {
      "cytosol": "#E8F4F8",
      "nucleus": "#E8F8E8"
    }

═════════════════════════════════════════════════════════════════════════════
STAGE 3: CONVERT → DocumentModel
═════════════════════════════════════════════════════════════════════════════

📍 Entry Point: PathwayConverter.convert()
📂 File: src/shypn/data/pathway/pathway_converter.py (line 554)

def convert(self, pathway: ProcessedPathwayData) -> DocumentModel:
    document = DocumentModel()
    
    # Convert species → places
    species_converter = SpeciesConverter(pathway, document)
    species_to_place = species_converter.convert()
    
    # Convert reactions → transitions
    reaction_converter = ReactionConverter(pathway, document, species_to_place)
    reaction_to_transition = reaction_converter.convert()
    
    # Convert stoichiometry → arcs
    arc_converter = ArcConverter(pathway, document, species_to_place, reaction_to_transition)
    arcs = arc_converter.convert()
    
    return document

───────────────────────────────────────────────────────────────────────────────
SUB-STAGE 3A: Species → Places
📂 File: src/shypn/data/pathway/pathway_converter.py (line 73)

class SpeciesConverter:
    def convert(self) -> Dict[str, Place]:
        species_to_place = {}
        
        for species in self.pathway.species:
            x, y = self.pathway.positions.get(species.id, (100.0, 100.0))
            
            # ⚠️ CRITICAL: Uses DocumentModel.create_place()
            # This method auto-assigns sequential IDs starting from _next_place_id
            place = self.document.create_place(x=x, y=y, label=species.name)
            
            # Set tokens
            place.set_tokens(species.initial_tokens)
            place.set_initial_marking(species.initial_tokens)
            
            # Store metadata
            place.metadata = {
                'species_id': species.id,
                'concentration': species.initial_concentration,
                'compartment': species.compartment
            }
            
            species_to_place[species.id] = place
        
        return species_to_place

ID Assignment:
  • DocumentModel._next_place_id starts at 1
  • First species → Place with id="1", name="P1"
  • Second species → Place with id="2", name="P2"
  • Etc.

Example:
  glucose (species) → Place(id="1", name="P1", label="Glucose", tokens=5, x=100, y=200)
  g6p (species)     → Place(id="2", name="P2", label="G6P", tokens=0, x=300, y=200)

───────────────────────────────────────────────────────────────────────────────
SUB-STAGE 3B: Reactions → Transitions
📂 File: src/shypn/data/pathway/pathway_converter.py (line 177)

class ReactionConverter:
    def convert(self) -> Dict[str, Transition]:
        reaction_to_transition = {}
        
        for reaction in self.pathway.reactions:
            x, y = self.pathway.positions.get(reaction.id, (100.0, 100.0))
            
            # ⚠️ CRITICAL: Uses DocumentModel.create_transition()
            # Auto-assigns sequential IDs from _next_transition_id
            transition = self.document.create_transition(x=x, y=y, label=reaction.name)
            
            # Determine transition type based on kinetic law
            if reaction.kinetic_law:
                if self._is_mass_action(reaction.kinetic_law):
                    transition.type = 'continuous'
                elif self._has_rate_formula(reaction.kinetic_law):
                    transition.type = 'continuous'
                else:
                    transition.type = 'immediate'
            else:
                transition.type = 'immediate'
            
            # Store rate function if continuous
            if transition.type == 'continuous' and reaction.kinetic_law:
                transition.rate_function = reaction.kinetic_law.formula
            
            # Store metadata
            transition.metadata = {
                'reaction_id': reaction.id,
                'reversible': reaction.reversible
            }
            
            reaction_to_transition[reaction.id] = transition
        
        return reaction_to_transition

ID Assignment:
  • DocumentModel._next_transition_id starts at 1
  • First reaction → Transition with id="1", name="T1"
  • Second reaction → Transition with id="2", name="T2"
  • Etc.

Example:
  hexokinase (reaction) → Transition(id="1", name="T1", label="Hexokinase", 
                                      type='continuous', rate_function="...")

───────────────────────────────────────────────────────────────────────────────
SUB-STAGE 3C: Stoichiometry → Arcs
📂 File: src/shypn/data/pathway/pathway_converter.py (line 471)

class ArcConverter:
    def convert(self) -> List[Arc]:
        arcs = []
        
        for reaction in self.pathway.reactions:
            transition = self.reaction_to_transition[reaction.id]
            
            # Reactants → Input arcs (Place → Transition)
            for species_id, stoichiometry in reaction.reactants:
                place = self.species_to_place[species_id]
                
                # ⚠️ CRITICAL: Uses DocumentModel.create_arc()
                # Auto-assigns sequential IDs from _next_arc_id
                arc = self.document.create_arc(
                    source=place,
                    target=transition,
                    weight=int(stoichiometry)
                )
                arcs.append(arc)
            
            # Products → Output arcs (Transition → Place)
            for species_id, stoichiometry in reaction.products:
                place = self.species_to_place[species_id]
                arc = self.document.create_arc(
                    source=transition,
                    target=place,
                    weight=int(stoichiometry)
                )
                arcs.append(arc)
        
        return arcs

ID Assignment:
  • DocumentModel._next_arc_id starts at 1
  • First arc → Arc with id="1", name="A1"
  • Second arc → Arc with id="2", name="A2"
  • Etc.

Example:
  glucose + ATP → G6P + ADP  (hexokinase reaction)
  
  Arcs created:
    Arc(id="1", name="A1", source=Place[glucose], target=Transition[hexokinase], weight=1)
    Arc(id="2", name="A2", source=Place[atp], target=Transition[hexokinase], weight=1)
    Arc(id="3", name="A3", source=Transition[hexokinase], target=Place[g6p], weight=1)
    Arc(id="4", name="A4", source=Transition[hexokinase], target=Place[adp], weight=1)

───────────────────────────────────────────────────────────────────────────────
OUTPUT: DocumentModel
📂 Structure: src/shypn/data/canvas/document_model.py

DocumentModel:
  ├─ places: List[Place]
  │  └─ Place(id, name, label, x, y, tokens, initial_marking, metadata)
  ├─ transitions: List[Transition]
  │  └─ Transition(id, name, label, x, y, type, rate_function, metadata)
  ├─ arcs: List[Arc]
  │  └─ Arc(id, name, source, target, weight)
  ├─ metadata: Dict
  │  ├─ source: "biochemical_pathway"
  │  ├─ pathway_name: "Glycolysis"
  │  ├─ species_count: 10
  │  ├─ reactions_count: 10
  │  └─ compartments: ["cytosol", "mitochondria"]
  └─ ID Counters:
     ├─ _next_place_id: 11 (after creating 10 places)
     ├─ _next_transition_id: 11 (after creating 10 transitions)
     └─ _next_arc_id: 25 (after creating 24 arcs)

═════════════════════════════════════════════════════════════════════════════
STAGE 4: SAVE FILES
═════════════════════════════════════════════════════════════════════════════

📍 Entry Point: _on_load_and_save_complete()
📂 File: src/shypn/helpers/sbml_import_panel.py (line 669)

def _on_load_and_save_complete(self, document_model, pathway_name):
    # 1. Save raw SBML file to project/pathways/
    filename = os.path.basename(self.current_filepath)
    pathways_dir = self.project.get_pathways_dir()
    dest_path = os.path.join(pathways_dir, filename)
    
    if not os.path.exists(dest_path):
        sbml_content = open(self.current_filepath, 'r').read()
        self.project.save_pathway_file(filename, sbml_content)
    
    # 2. Save .shy model file to project/models/
    base_name = os.path.splitext(filename)[0]
    model_filename = f"{base_name}.shy"
    models_dir = self.project.get_models_dir()
    model_filepath = os.path.join(models_dir, model_filename)
    
    # ⚠️ CRITICAL: Save DocumentModel to .shy file
    document_model.save_to_file(model_filepath)
    
    # 3. Create PathwayDocument metadata
    pathway_doc = PathwayDocument(
        source_type="sbml",
        source_id=base_name,
        source_organism=organism,
        name=pathway_name
    )
    pathway_doc.raw_file = filename
    pathway_doc.model_file = model_filename
    
    # 4. Register with project
    self.project.add_pathway(pathway_doc)
    self.project.save()

───────────────────────────────────────────────────────────────────────────────
SAVE: DocumentModel.save_to_file()
📂 File: src/shypn/data/canvas/document_model.py (line 475)

def save_to_file(self, filepath: str) -> None:
    data = self.to_dict()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

───────────────────────────────────────────────────────────────────────────────
SERIALIZE: DocumentModel.to_dict()
📂 File: src/shypn/data/canvas/document_model.py (line 364)

def to_dict(self) -> dict:
    """Serialize document to dictionary for JSON export."""
    return {
        "version": "2.0",
        "places": [place.to_dict() for place in self.places],
        "transitions": [transition.to_dict() for transition in self.transitions],
        "arcs": [arc.to_dict() for arc in self.arcs],
        "view_state": self.view_state
    }

Each object's to_dict() includes:
  • Place: id, name, label, x, y, tokens, initial_marking, metadata
  • Transition: id, name, label, x, y, type, rate_function, delay, priority, 
               firing_policy, metadata
  • Arc: id, name, source_id, target_id, weight, source_type, target_type

───────────────────────────────────────────────────────────────────────────────
OUTPUT: .shy File (JSON)
📂 Example: workspace/projects/SBML/models/BIOMD0000000001.shy

{
  "version": "2.0",
  "places": [
    {
      "id": "1",
      "name": "P1",
      "label": "Glucose",
      "x": 100.0,
      "y": 200.0,
      "tokens": 5,
      "initial_marking": 5,
      "metadata": {
        "species_id": "glucose",
        "concentration": 5.0,
        "compartment": "cytosol"
      }
    },
    ...
  ],
  "transitions": [
    {
      "id": "1",
      "name": "T1",
      "label": "Hexokinase",
      "x": 200.0,
      "y": 200.0,
      "type": "continuous",
      "rate_function": "k1 * glucose * atp",
      "firing_policy": "random",
      "metadata": {
        "reaction_id": "hexokinase",
        "reversible": false
      }
    },
    ...
  ],
  "arcs": [
    {
      "id": "1",
      "name": "A1",
      "source_id": "1",
      "target_id": "1",
      "source_type": "place",
      "target_type": "transition",
      "weight": 1
    },
    ...
  ]
}

═════════════════════════════════════════════════════════════════════════════
STAGE 5: LOAD FROM FILE (User opens .shy file later)
═════════════════════════════════════════════════════════════════════════════

📍 Entry Point: DocumentModel.load_from_file()
📂 File: src/shypn/data/canvas/document_model.py (line 484)

def load_from_file(cls, filepath: str) -> 'DocumentModel':
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return cls.from_dict(data)

───────────────────────────────────────────────────────────────────────────────
DESERIALIZE: DocumentModel.from_dict()
📂 File: src/shypn/data/canvas/document_model.py (line 409)

@classmethod
def from_dict(cls, data: dict) -> 'DocumentModel':
    document = cls()
    
    # Restore places
    max_place_id = 0
    for place_data in data.get("places", []):
        place = Place.from_dict(place_data)
        document.places.append(place)
        
        # ⚠️ CRITICAL: Track max ID to update counter
        place_id_int = int(place.id)
        max_place_id = max(max_place_id, place_id_int)
    
    # Restore transitions
    max_transition_id = 0
    for transition_data in data.get("transitions", []):
        transition = Transition.from_dict(transition_data)
        document.transitions.append(transition)
        
        transition_id_int = int(transition.id)
        max_transition_id = max(max_transition_id, transition_id_int)
    
    # Restore arcs
    max_arc_id = 0
    for arc_data in data.get("arcs", []):
        arc = Arc.from_dict(arc_data, places_dict, transitions_dict)
        document.arcs.append(arc)
        
        arc_id_int = int(arc.id)
        max_arc_id = max(max_arc_id, arc_id_int)
    
    # ⚠️ CRITICAL FIX: Update ID counters to prevent duplicates
    document._next_place_id = max_place_id + 1
    document._next_transition_id = max_transition_id + 1
    document._next_arc_id = max_arc_id + 1
    
    return document

═════════════════════════════════════════════════════════════════════════════
KEY FINDINGS
═════════════════════════════════════════════════════════════════════════════

## ID Generation Flow

### During SBML Conversion (Stage 3)

1. **DocumentModel starts with default counters:**
   ```python
   _next_place_id = 1
   _next_transition_id = 1
   _next_arc_id = 1
   ```

2. **Converters call create_* methods:**
   ```python
   # SpeciesConverter
   for species in pathway.species:
       place = document.create_place(x, y, label)  # Gets ID from counter, increments
   
   # ReactionConverter  
   for reaction in pathway.reactions:
       transition = document.create_transition(x, y, label)  # Gets ID from counter, increments
   
   # ArcConverter
   for reactant/product pair:
       arc = document.create_arc(source, target, weight)  # Gets ID from counter, increments
   ```

3. **Sequential ID assignment:**
   ```
   BIOMD0000000001 (12 species, 17 reactions):
   Places:      IDs 1-12   (counter ends at 13)
   Transitions: IDs 1-17   (counter ends at 18)
   Arcs:        IDs 1-66   (counter ends at 67)
   ```

4. **IDs saved as strings in JSON:**
   ```json
   {
     "id": "1",  ← Stored as string
     "name": "P1"
   }
   ```

### During File Load (Stage 5)

5. **IDs loaded from JSON:**
   ```python
   place = Place.from_dict(place_data)  # place.id = "1" (string)
   document.places.append(place)
   ```

6. **⚠️ CRITICAL FIX: Counter update:**
   ```python
   max_place_id = max([int(p.id) for p in document.places])
   document._next_place_id = max_place_id + 1
   ```
   
   Without this fix:
   - Counter stays at 1
   - Next manually created place gets ID 1 (duplicate!)
   - Simulation confuses the two places with same ID
   - Result: Phantom values in unconnected places

## Complete File Paths

```
workspace/
└─ projects/
   └─ SBML/
      ├─ pathways/
      │  └─ BIOMD0000000001.xml     ← Raw SBML file
      └─ models/
         └─ BIOMD0000000001.shy     ← Converted Petri net (JSON)
```

## Data Transformations Summary

| Stage | Input | Output | Key Operations |
|-------|-------|--------|----------------|
| Parse | SBML XML | PathwayData | Extract species, reactions, parameters |
| Post-Process | PathwayData | ProcessedPathwayData | Add positions, colors, normalize tokens |
| Convert | ProcessedPathwayData | DocumentModel | Create places, transitions, arcs with IDs |
| Save | DocumentModel | .shy JSON | Serialize all objects with IDs |
| Load | .shy JSON | DocumentModel | Deserialize objects, **update ID counters** |

## Critical Bug Fix (October 27, 2025)

**Issue:** Duplicate IDs after loading SBML models  
**Cause:** `from_dict()` didn't update `_next_*_id` counters  
**Fix:** Track max ID for each type, set counter to `max_id + 1`  
**Impact:** Prevents phantom values in manually created objects  

See: `doc/DUPLICATE_ID_BUG_FIX.md`
