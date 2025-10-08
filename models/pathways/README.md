# KEGG Pathways

This directory contains parsed KEGG pathways for testing and reference.

## File Naming Convention

Files are named using the KEGG pathway ID:
- `<pathway_id>.kgml` - Raw KGML XML from KEGG
- `<pathway_id>.shy` - Converted Petri net model

## Example Pathways

### Human (hsa) Pathways
- `hsa00010` - Glycolysis / Gluconeogenesis
- `hsa00020` - TCA Cycle (Citric acid cycle)
- `hsa00030` - Pentose phosphate pathway

### Reference (map) Pathways
- `map00010` - Glycolysis (organism-independent)
- `map00020` - TCA Cycle (organism-independent)

## Usage

### Fetch and Save a Pathway

```python
from shypn.importer.kegg import KEGGAPIClient

client = KEGGAPIClient()
kgml = client.fetch_kgml("hsa00010")

with open("models/pathways/hsa00010.kgml", "w") as f:
    f.write(kgml)
```

### Parse and Convert

```python
from shypn.importer.kegg import parse_kgml
from shypn.importer.kegg.converter import KEGGConverter

with open("models/pathways/hsa00010.kgml", "r") as f:
    kgml = f.read()

pathway = parse_kgml(kgml)
converter = KEGGConverter()
document = converter.convert(pathway)

document.save_to_file("models/pathways/hsa00010.shy")
```

## ⚠️ Academic Use Only

These pathways are from the KEGG database, which is provided for academic use only.
Please comply with KEGG's usage policies and cite appropriately:

> Kanehisa, M. and Goto, S.; KEGG: Kyoto Encyclopedia of Genes and Genomes.
> Nucleic Acids Res. 28, 27-30 (2000).

## Notes

- KGML files are periodically updated by KEGG
- Files here are snapshots for testing/reference
- To get the latest version, fetch directly from KEGG API
