#!/usr/bin/env python3
"""Test signal classification with actual model."""

import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(message)s')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.importer.bigg.bigg_downloader import BiGGDownloader
from shypn.importer.bigg.bigg_signal_classifier import BiGGSignalClassifier
from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.netobjs.signal_type import SignalType

# Download and parse
downloader = BiGGDownloader()
parser = SBMLParser()
postprocessor = PathwayPostProcessor()
converter = PathwayConverter()
classifier = BiGGSignalClassifier()

print("Downloading...")
sbml_path = downloader.download_sbml("e_coli_core", use_cache=True)

print("Parsing...")
parsed = parser.parse_file(sbml_path)
processed = postprocessor.process(parsed)
document = converter.convert(processed)

print(f"\nDocument has {len(document.places)} places")
print("\nFirst 5 places:")
for i, place in enumerate(document.places[:5]):
    print(f"  {i+1}. {place.label} - original_species_id: {place.metadata.get('original_species_id', 'NONE')}")

print("\nClassifying...")
classified = classifier.classify_energy_signals(document.places)

energy_places = [p for p in classified if hasattr(p, 'signal_type') and p.signal_type == SignalType.ENERGY]
print(f"\nFound {len(energy_places)} energy signals:")
for p in energy_places[:10]:
    print(f"  - {p.label} (bigg_id: {p.metadata.get('original_species_id', 'NONE')})")
