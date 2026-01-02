#!/usr/bin/env python3
"""Debug script to test enrichment on hsa00010 model."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.services.enrichment.stoichiometry import KEGGStoichiometryEnricher

# Load model
model_path = 'workspace/projects/My_Project/models/hsa00010.shy'
print(f"Loading model from: {model_path}")

# Load using DocumentModel's built-in method
document = DocumentModel.load_from_file(model_path)

print(f"\nBefore enrichment:")
print(f"  Places: {len(document.places)}")
print(f"  Transitions: {len(document.transitions)}")
print(f"  Arcs: {len(document.arcs)}")
enriched_before = getattr(document, 'metadata', {}).get('stoichiometry_enriched', False) if hasattr(document, 'metadata') else False
print(f"  Metadata enriched: {enriched_before}")

# Run enrichment
print(f"\nRunning enrichment...")
enricher = KEGGStoichiometryEnricher()
result = enricher.enrich_document(document)

print(f"\nEnrichment result:")
print(f"  Success: {result.success}")
print(f"  Message: {result.message}")
print(f"  Duration: {result.duration_seconds:.2f}s")
print(f"  Statistics:")
for key, value in result.statistics.items():
    print(f"    {key}: {value}")

print(f"\nAfter enrichment:")
print(f"  Places: {len(document.places)}")
print(f"  Transitions: {len(document.transitions)}")
print(f"  Arcs: {len(document.arcs)}")
enriched_after = getattr(document, 'metadata', {}).get('stoichiometry_enriched', False) if hasattr(document, 'metadata') else False
print(f"  Metadata enriched: {enriched_after}")

# Check for enriched places
enriched_places = [p for p in document.places 
                   if p.metadata and p.metadata.get('source') == 'stoichiometry_enrichment']
print(f"  Places with source='stoichiometry_enrichment': {len(enriched_places)}")

if enriched_places:
    print(f"\nSample enriched places:")
    for p in enriched_places[:10]:
        print(f"  • {p.name} ({p.metadata.get('kegg_id', 'no ID')})")

# Save enriched model
output_path = 'workspace/projects/My_Project/models/hsa00010_enriched_test.shy'
print(f"\nSaving enriched model to: {output_path}")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(document.to_dict(), f, indent=2)
print("✅ Done!")
