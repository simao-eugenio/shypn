# KEGG Pathway Import Documentation

This directory contains comprehensive documentation for the KEGG pathway import feature in shypn.

## Documentation Files

### Quick References

- **[INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)** - 🎉 Integration status and testing
  - What was integrated
  - How to test
  - Panel lifecycle
  - Best for: Knowing what's ready to use

- **[PANEL_INTEGRATION_GUIDE.md](PANEL_INTEGRATION_GUIDE.md)** - 🎯 Panel behavior guide
  - Mutual exclusivity with Analyses panel
  - Toggle button behavior
  - Float/dock controls
  - Workflow examples
  - Best for: Understanding panel interactions

- **[WINDOW_CLOSE_FIX.md](WINDOW_CLOSE_FIX.md)** - 🔧 Segmentation fault fix
  - Fixed window close crash (Exit Code 139)
  - delete-event handler implementation
  - Testing verification
  - Best for: Understanding the close behavior fix

- **[BUGFIX_ENTRIES_ITERATION.md](BUGFIX_ENTRIES_ITERATION.md)** - 🐛 Entries iteration fix
  - Fixed 'str' has no attribute 'type' error
  - Dictionary .values() iteration
  - Testing verification
  - Best for: Understanding the fetch error fix

- **[BUGFIX_CONVERSION_OPTIONS_PARAMETER.md](BUGFIX_CONVERSION_OPTIONS_PARAMETER.md)** - 🐛 Parameter name fix
  - Fixed 'unexpected keyword argument filter_cofactors' error
  - Correct parameter naming (include_cofactors)
  - Testing verification
  - Best for: Understanding the import error fix

- **[KEGG_IMPORT_QUICK_REFERENCE.md](KEGG_IMPORT_QUICK_REFERENCE.md)** - ⚡ One-page cheat sheet
  - Quick start guide
  - Code snippets
  - Common patterns
  - Best for: Developers who need quick answers

### Technical Documentation

- **[KEGG_PATHWAY_IMPORT_ANALYSIS.md](KEGG_PATHWAY_IMPORT_ANALYSIS.md)** - Technical deep dive
  - KGML format analysis
  - Mapping strategies (compounds→places, reactions→transitions)
  - Coordinate systems and scaling
  - Cofactor handling
  - Best for: Understanding the conversion algorithm

- **[KEGG_PATHWAY_IMPORT_PLAN.md](KEGG_PATHWAY_IMPORT_PLAN.md)** - Implementation roadmap
  - 5-phase development plan
  - Module architecture
  - API design decisions
  - Testing strategy
  - Best for: Understanding the development process

- **[KEGG_PATHWAY_IMPORT_SUMMARY.md](KEGG_PATHWAY_IMPORT_SUMMARY.md)** - Executive overview
  - Feature overview
  - Key capabilities
  - Use cases
  - Academic use requirements
  - Best for: High-level understanding

### Progress Tracking

- **[KEGG_IMPORT_PROGRESS.md](KEGG_IMPORT_PROGRESS.md)** - Development status
  - Completed features
  - Work in progress
  - Remaining tasks
  - Code statistics
  - Test results
  - Best for: Tracking implementation status

## Feature Overview

The KEGG pathway import feature allows importing biochemical pathways from the KEGG database into shypn as Petri net models.

### Key Capabilities

✅ **Implemented**:
- Fetch pathways from KEGG REST API
- Parse KGML XML format
- Convert biochemical pathways to Petri nets
- Map compounds to places
- Map reactions to transitions
- Create substrate/product arcs
- Coordinate scaling and layout
- Cofactor filtering
- OOP architecture with base classes
- Comprehensive test suite

🔄 **In Progress**:
- GTK import dialog UI
- Dockable pathway panel

⬜ **Future**:
- Metadata preservation in objects
- Regulatory relations (test arcs)
- User documentation

## Quick Start

### Using the API

```python
from shypn.importer.kegg import KEGGAPIClient, KGMLParser, PathwayConverter

# Fetch pathway
client = KEGGAPIClient()
kgml_data = client.fetch_kgml("hsa00010")  # Glycolysis

# Parse KGML
parser = KGMLParser()
pathway = parser.parse(kgml_data)

# Convert to Petri net
converter = PathwayConverter()
document_model = converter.convert(pathway)

# Save
document_model.save("glycolysis.shy")
```

### Using the UI (Coming Soon)

1. Open **Pathway Operations** panel
2. Go to **Import** tab
3. Enter pathway ID (e.g., "hsa00010")
4. Click **Fetch Pathway**
5. Review preview
6. Adjust options if needed
7. Click **Import**

## Architecture

### Backend (Core Logic)

```
src/shypn/importer/kegg/
├── api_client.py          # KEGG REST API client
├── kgml_parser.py         # KGML XML parser
├── models.py              # Data classes
├── converter_base.py      # Base classes & strategies
├── compound_mapper.py     # Compound → Place
├── reaction_mapper.py     # Reaction → Transition
├── arc_builder.py         # Arc creation
└── pathway_converter.py   # Main converter
```

### Frontend (UI)

```
ui/panels/pathway_panel.ui              # GTK UI definition
src/shypn/helpers/pathway_panel_loader.py    # Panel loader
src/shypn/ui/panels/kegg_import_panel.py     # Import controller
```

### Documentation

```
doc/KEGG/
├── README.md                          # This file
├── KEGG_IMPORT_QUICK_REFERENCE.md     # Cheat sheet
├── KEGG_PATHWAY_IMPORT_ANALYSIS.md    # Technical details
├── KEGG_PATHWAY_IMPORT_PLAN.md        # Implementation plan
├── KEGG_PATHWAY_IMPORT_SUMMARY.md     # Executive summary
└── KEGG_IMPORT_PROGRESS.md            # Status tracking
```

## Sample Data

Sample pathways are stored in `models/pathways/`:

- **hsa00010** - Glycolysis (31 places, 34 transitions)
- **hsa00020** - TCA Cycle (23 places, 22 transitions)
- **hsa00030** - Pentose Phosphate (40 places, 26 transitions)

Each pathway has both KGML (`.kgml`) and converted Petri net (`.shy`) files.

## Testing

### Unit Tests

```bash
# Test API client
python3 tests/test_kegg_api.py

# Test KGML parser
python3 tests/test_kegg_kgml_parser.py

# Test conversion
python3 tests/test_kegg_conversion.py

# Test with saved pathways
python3 tests/test_kegg_pathways_from_files.py
```

### Manual Testing

```bash
# Fetch a pathway
python3 scripts/fetch_kegg_pathway.py hsa00010

# Convert and save
python3 -c "
from shypn.importer.kegg import KEGGAPIClient, KGMLParser, PathwayConverter

client = KEGGAPIClient()
parser = KGMLParser()
converter = PathwayConverter()

kgml = client.fetch_kgml('hsa00010')
pathway = parser.parse(kgml)
doc = converter.convert(pathway)
doc.save('test_glycolysis.shy')
print(f'Saved: {len(doc.places)} places, {len(doc.transitions)} transitions')
"
```

## Academic Use Notice

⚠️ **Important**: KEGG data is freely available for academic use only. Commercial use requires a license from Kanehisa Laboratories.

When using KEGG data, please cite:
- Kanehisa, M. and Goto, S.; KEGG: Kyoto Encyclopedia of Genes and Genomes. Nucleic Acids Res. 28, 27-30 (2000).

## Contributing

When working on KEGG import features:

1. **Backend changes** → Update corresponding docs in `KEGG_PATHWAY_IMPORT_ANALYSIS.md`
2. **API changes** → Update examples in `KEGG_IMPORT_QUICK_REFERENCE.md`
3. **Progress updates** → Update `KEGG_IMPORT_PROGRESS.md`
4. **New features** → Update `KEGG_PATHWAY_IMPORT_SUMMARY.md`

## Support

For issues or questions:
- Check existing documentation in this directory
- Review test files in `tests/test_kegg_*.py`
- Examine sample pathways in `models/pathways/`

## Next Steps

See [KEGG_IMPORT_PROGRESS.md](KEGG_IMPORT_PROGRESS.md) for current status and roadmap.
