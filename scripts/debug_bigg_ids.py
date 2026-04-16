#!/usr/bin/env python3
"""Debug script to inspect BiGG place IDs."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.importer.bigg.bigg_downloader import BiGGDownloader
from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter

# Download and parse e_coli_core
downloader = BiGGDownloader()
parser = SBMLParser()
postprocessor = PathwayPostProcessor()
converter = PathwayConverter()

print("Downloading e_coli_core...")
sbml_path = downloader.download_sbml("e_coli_core", use_cache=True)

print("Parsing...")
parsed = parser.parse_file(sbml_path)

print(f"\nFirst 10 species IDs:")
for i, species in enumerate(parsed.species[:10]):
    print(f"  {i+1}. {species.id} (name: {species.name})")

print("\nConverting to Petri net...")
processed = postprocessor.process(parsed)
document = converter.convert(processed)

print(f"\nFirst 10 place metadata:")
for i, place in enumerate(document.places[:10]):
    orig_id = place.metadata.get('original_species_id', 'NOT_SET')
    print(f"  {i+1}. name={place.name}, label={place.label}, original_species_id={orig_id}")

print("\nChecking for ATP-like species:")
for species in parsed.species:
    if 'atp' in species.id.lower():
        print(f"  Found: {species.id} (name: {species.name})")
