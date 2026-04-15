#!/usr/bin/env python3
"""
Comprehensive Test Suite for 100 BioModels SBML Import

This script systematically tests Shypn's import capabilities across
100 curated SBML models from BioModels Database.

Purpose:
  - Validate SBML import robustness
  - Measure conversion accuracy (species → places, reactions → transitions)
  - Assess kinetic parameter extraction
  - Evaluate layout generation quality
  - Document results for thesis/paper

Results are saved to: doc/thesis/sbml_models/

Author: Shypn Development Team
Date: November 2025
"""

import sys
import os
import json
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

# Add src to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor


@dataclass
class ModelTestResult:
    """Results from testing a single SBML model."""
    model_id: str
    model_name: str
    success: bool
    
    # Import metrics
    parse_success: bool
    parse_time: float
    parse_error: Optional[str]
    
    # Model statistics
    species_count: int
    reactions_count: int
    compartments_count: int
    parameters_count: int
    
    # Conversion metrics
    places_created: int
    transitions_created: int
    arcs_created: int
    test_arcs_created: int
    inhibitor_arcs_created: int
    
    # Kinetic parameters
    has_kinetics: bool
    continuous_transitions: int
    stochastic_transitions: int
    kinetic_laws_parsed: int
    
    # Layout metrics
    layout_generated: bool
    layout_time: float
    positions_assigned: int
    
    # Quality metrics
    initial_tokens_sum: float
    has_modifiers: bool
    has_reversible_reactions: bool
    
    # Error details
    errors: List[str]
    warnings: List[str]


class BioModels100TestSuite:
    """Test suite for 100 BioModels SBML files."""
    
    # Curated list of 100 models organized by complexity
    MODELS_CATALOG = [
        # === SIMPLE MODELS (1-10) ===
        ("BIOMD0000000001", "Edelstein1996 - EPSP ACh event", "simple"),
        ("BIOMD0000000002", "Kholodenko2000 - MAPK feedback oscillations", "simple"),
        ("BIOMD0000000003", "Goldbeter1991 - Cell cycle", "simple"),
        ("BIOMD0000000004", "Gardner1998 - Toggle switch", "simple"),
        ("BIOMD0000000005", "Tyson1991 - Cell cycle", "simple"),
        ("BIOMD0000000012", "Elowitz2000 - Repressilator", "simple"),
        ("BIOMD0000000021", "Vilar2002 - Circadian clock", "simple"),
        ("BIOMD0000000026", "Ferrell1998 - MAPK bistability", "simple"),
        ("BIOMD0000000028", "Goldbeter1996 - Drosophila circadian", "simple"),
        ("BIOMD0000000031", "Novak2001 - Cell cycle checkpoint", "simple"),
        
        # === MEDIUM COMPLEXITY (11-40) ===
        ("BIOMD0000000010", "Kholodenko2000 - MAPK cascade", "medium"),
        ("BIOMD0000000033", "Tyson1991 - Cell division", "medium"),
        ("BIOMD0000000035", "Leloup1999 - Circadian rhythm", "medium"),
        ("BIOMD0000000048", "Schoeberl2002 - EGF signaling", "medium"),
        ("BIOMD0000000051", "Goldbeter1991 - Mitotic oscillator", "medium"),
        ("BIOMD0000000061", "Bagci2006 - p53 PTEN", "medium"),
        ("BIOMD0000000064", "Goldbeter1995 - Calcium oscillations", "medium"),
        ("BIOMD0000000070", "Goldbeter2006 - NF-kB signaling", "medium"),
        ("BIOMD0000000074", "Proctor2008 - p53 ATM", "medium"),
        ("BIOMD0000000089", "Vasalou2009 - Circadian pacemaker", "medium"),
        ("BIOMD0000000091", "Conradie2010 - PDGF signaling", "medium"),
        ("BIOMD0000000102", "Hatzimanikatis1999 - Tryptophan biosynthesis", "medium"),
        ("BIOMD0000000103", "Rohwer2001 - Glycolysis", "medium"),
        ("BIOMD0000000105", "Nielsen1998 - Galactose regulation", "medium"),
        ("BIOMD0000000108", "Dano1999 - Glycolysis oscillations", "medium"),
        ("BIOMD0000000116", "Nikolaev2010 - ERK MAPK", "medium"),
        ("BIOMD0000000120", "Komarova2003 - Bone remodeling", "medium"),
        ("BIOMD0000000137", "Chickarmane2008 - Stem cell switching", "medium"),
        ("BIOMD0000000145", "Chickarmane2006 - Cell differentiation", "medium"),
        ("BIOMD0000000156", "Akman2008 - Circadian rhythm", "medium"),
        ("BIOMD0000000162", "Tian2007 - Calcium oscillations", "medium"),
        ("BIOMD0000000170", "Smallbone2011 - Yeast glycolysis", "medium"),
        ("BIOMD0000000171", "Pritchard2002 - Glycolysis", "medium"),
        ("BIOMD0000000174", "Ung2008 - Purine metabolism", "medium"),
        ("BIOMD0000000189", "Hoefnagel2002 - Pyruvate metabolism", "medium"),
        ("BIOMD0000000191", "Becker2010 - EGF receptor", "medium"),
        ("BIOMD0000000201", "Singh2006 - STAT5 homodimerization", "medium"),
        ("BIOMD0000000203", "Rateitschak2009 - NF-kB pathway", "medium"),
        ("BIOMD0000000204", "Zi2005 - EGFR signaling", "medium"),
        ("BIOMD0000000206", "Teusink2000 - Glycolysis yeast", "medium"),
        
        # === COMPLEX MODELS (41-70) ===
        ("BIOMD0000000211", "Cooling2009 - Circadian clock", "complex"),
        ("BIOMD0000000217", "Sivakumar2011 - Notch signaling", "complex"),
        ("BIOMD0000000219", "Koenig2012 - Hepatic glucose", "complex"),
        ("BIOMD0000000231", "Tan2012 - Antibiotic treatment", "complex"),
        ("BIOMD0000000232", "Wodarz2007 - HIV dynamics", "complex"),
        ("BIOMD0000000239", "Zi2011 - VEGF signaling", "complex"),
        ("BIOMD0000000242", "Rao2004 - Interferon signaling", "complex"),
        ("BIOMD0000000244", "Cho2003 - Cell cycle", "complex"),
        ("BIOMD0000000245", "Haberichter2007 - Circadian rhythm", "complex"),
        ("BIOMD0000000259", "Millat2013 - Solventogenesis", "complex"),
        ("BIOMD0000000267", "Begitt2014 - JAK-STAT signaling", "complex"),
        ("BIOMD0000000273", "Nguyen2014 - TNF signaling", "complex"),
        ("BIOMD0000000280", "Begitt2014 - STAT activation", "complex"),
        ("BIOMD0000000281", "Begitt2014 - Interferon", "complex"),
        ("BIOMD0000000289", "Chassagnole2002 - Carbon metabolism", "complex"),
        ("BIOMD0000000290", "Kotte2010 - E. coli metabolism", "complex"),
        ("BIOMD0000000294", "Xu2011 - p53 dynamics", "complex"),
        ("BIOMD0000000297", "Calzone2010 - ERBB signaling", "complex"),
        ("BIOMD0000000301", "Schliemann2011 - Iron metabolism", "complex"),
        ("BIOMD0000000308", "Marhl2000 - Calcium oscillations", "complex"),
        ("BIOMD0000000316", "Chen2004 - EGFR signaling", "complex"),
        ("BIOMD0000000320", "Conradie2010 - PDGF pathway", "complex"),
        ("BIOMD0000000323", "Zi2008 - MAPK signaling", "complex"),
        ("BIOMD0000000329", "Borisov2009 - ErbB signaling", "complex"),
        ("BIOMD0000000335", "Kolch2005 - RAF signaling", "complex"),
        ("BIOMD0000000347", "Cooling2008 - Cardiac metabolism", "complex"),
        ("BIOMD0000000354", "Lavrentovich2008 - Tumor growth", "complex"),
        ("BIOMD0000000366", "Kholodenko2010 - MAPK signaling", "complex"),
        ("BIOMD0000000370", "Birtwistle2007 - EGFR signaling", "complex"),
        ("BIOMD0000000375", "Friedman2009 - Cancer immunotherapy", "complex"),
        
        # === VERY COMPLEX MODELS (71-100) ===
        ("BIOMD0000000383", "Bhalla2002 - MAPK feedback", "very_complex"),
        ("BIOMD0000000390", "Nakakuki2010 - EGF signaling", "very_complex"),
        ("BIOMD0000000395", "Mager2003 - Chemotherapy", "very_complex"),
        ("BIOMD0000000400", "Sturrock2011 - Wound healing", "very_complex"),
        ("BIOMD0000000410", "Ayati2010 - Bone remodeling", "very_complex"),
        ("BIOMD0000000420", "Tham2008 - Hepatic glucose", "very_complex"),
        ("BIOMD0000000426", "vanRiel2013 - Amino acid metabolism", "very_complex"),
        ("BIOMD0000000428", "Vera2007 - Wound healing", "very_complex"),
        ("BIOMD0000000441", "Arnold2014 - Interferon signaling", "very_complex"),
        ("BIOMD0000000448", "Raia2011 - ErbB signaling", "very_complex"),
        ("BIOMD0000000450", "Rao2014 - JAK-STAT pathway", "very_complex"),
        ("BIOMD0000000451", "Ung2008 - Purine salvage", "very_complex"),
        ("BIOMD0000000461", "Smallbone2013 - Glycolysis", "very_complex"),
        ("BIOMD0000000471", "Heldt2018 - Cell cycle", "very_complex"),
        ("BIOMD0000000479", "Novak2008 - Cell cycle checkpoint", "very_complex"),
        ("BIOMD0000000482", "Pandey2011 - IGF signaling", "very_complex"),
        ("BIOMD0000000491", "Gao2013 - Yeast cell cycle", "very_complex"),
        ("BIOMD0000000500", "Zi2014 - Receptor signaling", "very_complex"),
        ("BIOMD0000000507", "Proctor2017 - Circadian clock", "very_complex"),
        ("BIOMD0000000517", "Ratushny2012 - TOR signaling", "very_complex"),
        ("BIOMD0000000523", "Jarrett2018 - Cardiac metabolism", "very_complex"),
        ("BIOMD0000000531", "Smallbone2013 - Central metabolism", "very_complex"),
        ("BIOMD0000000540", "Stanford2013 - HIF signaling", "very_complex"),
        ("BIOMD0000000549", "Zi2013 - Signaling crosstalk", "very_complex"),
        ("BIOMD0000000556", "vanEunen2012 - Yeast glycolysis", "very_complex"),
        ("BIOMD0000000562", "Chen2013 - Cell migration", "very_complex"),
        ("BIOMD0000000574", "Marmiesse2015 - Starch metabolism", "very_complex"),
        ("BIOMD0000000581", "Maeda2006 - Circadian rhythm", "very_complex"),
        ("BIOMD0000000590", "Proctor2013 - p53 Mdm2", "very_complex"),
        ("BIOMD0000000600", "Heldt2018 - Mitotic spindle", "very_complex"),
    ]
    
    def __init__(self, output_dir: Path):
        """Initialize test suite.
        
        Args:
            output_dir: Directory for test results (doc/thesis/sbml_models/)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results: List[ModelTestResult] = []
        self.start_time = datetime.now()
        
        # Initialize components
        self.parser = SBMLParser()
        self.converter = PathwayConverter()
        self.postprocessor = PathwayPostProcessor(scale_factor=10.0)
        
    def test_single_model(self, model_id: str, model_name: str, complexity: str) -> ModelTestResult:
        """Test import of a single SBML model.
        
        Args:
            model_id: BioModels ID (e.g., BIOMD0000000001)
            model_name: Model description
            complexity: Model complexity category
            
        Returns:
            ModelTestResult with comprehensive metrics
        """
        print(f"\n{'='*70}")
        print(f"Testing: {model_id}")
        print(f"Name: {model_name}")
        print(f"Complexity: {complexity}")
        print(f"{'='*70}")
        
        result = ModelTestResult(
            model_id=model_id,
            model_name=model_name,
            success=False,
            parse_success=False,
            parse_time=0.0,
            parse_error=None,
            species_count=0,
            reactions_count=0,
            compartments_count=0,
            parameters_count=0,
            places_created=0,
            transitions_created=0,
            arcs_created=0,
            test_arcs_created=0,
            inhibitor_arcs_created=0,
            has_kinetics=False,
            continuous_transitions=0,
            stochastic_transitions=0,
            kinetic_laws_parsed=0,
            layout_generated=False,
            layout_time=0.0,
            positions_assigned=0,
            initial_tokens_sum=0.0,
            has_modifiers=False,
            has_reversible_reactions=False,
            errors=[],
            warnings=[]
        )
        
        try:
            # Step 1: Fetch and parse SBML
            print(f"Step 1: Fetching and parsing SBML...")
            parse_start = time.time()
            
            try:
                # Try to fetch from BioModels
                import urllib.request
                import tempfile
                
                url = f"https://www.ebi.ac.uk/biomodels/model/download/{model_id}?filename={model_id}_url.xml"
                
                with urllib.request.urlopen(url, timeout=30) as response:
                    sbml_content = response.read()
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=False) as f:
                    f.write(sbml_content)
                    temp_path = Path(f.name)
                
                # Parse SBML
                pathway_data = self.parser.parse_file(str(temp_path))
                temp_path.unlink()  # Clean up
                
                result.parse_time = time.time() - parse_start
                result.parse_success = True
                
                print(f"  ✓ Parsed successfully in {result.parse_time:.2f}s")
                
            except Exception as e:
                result.parse_time = time.time() - parse_start
                result.parse_error = str(e)
                result.errors.append(f"Parse failed: {e}")
                print(f"  ✗ Parse failed: {e}")
                return result
            
            # Step 2: Extract model statistics
            print(f"Step 2: Extracting model statistics...")
            
            result.species_count = len(pathway_data.species)
            result.reactions_count = len(pathway_data.reactions)
            result.compartments_count = len(pathway_data.compartments) if hasattr(pathway_data, 'compartments') else 0
            result.parameters_count = len(pathway_data.parameters) if hasattr(pathway_data, 'parameters') else 0
            
            print(f"  Species: {result.species_count}")
            print(f"  Reactions: {result.reactions_count}")
            print(f"  Compartments: {result.compartments_count}")
            print(f"  Parameters: {result.parameters_count}")
            
            # Check for modifiers and reversible reactions
            for reaction in pathway_data.reactions:
                if hasattr(reaction, 'modifiers') and reaction.modifiers:
                    result.has_modifiers = True
                if hasattr(reaction, 'reversible') and reaction.reversible:
                    result.has_reversible_reactions = True
            
            # Step 3: Post-process pathway data
            print(f"Step 3: Post-processing pathway data...")
            
            try:
                processed_data = self.postprocessor.process(pathway_data)
                print(f"  ✓ Post-processed successfully")
                
            except Exception as e:
                result.errors.append(f"Post-processing failed: {e}")
                print(f"  ✗ Post-processing failed: {e}")
                return result
            
            # Step 4: Convert to Petri net
            print(f"Step 4: Converting to Petri net...")
            
            try:
                document_model = self.converter.convert(processed_data)
                
                # Extract objects from document model
                places = document_model.places
                transitions = document_model.transitions
                arcs = document_model.arcs
                
                result.places_created = len(places)
                result.transitions_created = len(transitions)
                
                # Count arc types
                for arc in arcs:
                    if hasattr(arc, 'arc_type'):
                        if arc.arc_type == 'test':
                            result.test_arcs_created += 1
                        elif arc.arc_type == 'inhibitor':
                            result.inhibitor_arcs_created += 1
                        else:
                            result.arcs_created += 1
                    else:
                        result.arcs_created += 1
                
                print(f"  ✓ Places: {result.places_created}")
                print(f"  ✓ Transitions: {result.transitions_created}")
                print(f"  ✓ Normal arcs: {result.arcs_created}")
                print(f"  ✓ Test arcs: {result.test_arcs_created}")
                print(f"  ✓ Inhibitor arcs: {result.inhibitor_arcs_created}")
                
            except Exception as e:
                result.errors.append(f"Conversion failed: {e}")
                print(f"  ✗ Conversion failed: {e}")
                return result
            
            # Step 5: Analyze kinetics
            print(f"Step 5: Analyzing kinetic parameters...")
            
            for transition in transitions:
                if hasattr(transition, 'transition_type'):
                    if transition.transition_type == 'continuous':
                        result.continuous_transitions += 1
                        result.has_kinetics = True
                    elif transition.transition_type == 'stochastic':
                        result.stochastic_transitions += 1
                
                if hasattr(transition, 'kinetic_law') and transition.kinetic_law:
                    result.kinetic_laws_parsed += 1
            
            print(f"  Continuous transitions: {result.continuous_transitions}")
            print(f"  Stochastic transitions: {result.stochastic_transitions}")
            print(f"  Kinetic laws parsed: {result.kinetic_laws_parsed}")
            
            # Step 6: Check layout
            print(f"Step 6: Checking layout...")
            
            # Check if positions were assigned during post-processing
            result.positions_assigned = len(processed_data.positions) if hasattr(processed_data, 'positions') else 0
            result.layout_generated = result.positions_assigned > 0
            
            print(f"  ✓ Positions assigned: {result.positions_assigned}")
            
            # Step 7: Calculate initial tokens
            print(f"Step 7: Checking initial markings...")
            
            for place in places:
                if hasattr(place, 'initial_tokens'):
                    result.initial_tokens_sum += place.initial_tokens
            
            print(f"  Total initial tokens: {result.initial_tokens_sum:.2f}")
            
            # Mark as successful
            result.success = True
            print(f"\n✅ SUCCESS: {model_id} imported successfully")
            
        except Exception as e:
            result.errors.append(f"Unexpected error: {e}")
            print(f"\n❌ FAILED: {model_id}")
            print(f"Error: {e}")
            traceback.print_exc()
        
        return result
    
    def run_all_tests(self, limit: Optional[int] = None):
        """Run tests on all models in catalog.
        
        Args:
            limit: Optional limit on number of models to test
        """
        models_to_test = self.MODELS_CATALOG[:limit] if limit else self.MODELS_CATALOG
        
        print(f"\n{'='*70}")
        print(f"BioModels 100 Test Suite")
        print(f"{'='*70}")
        print(f"Models to test: {len(models_to_test)}")
        print(f"Output directory: {self.output_dir}")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        for i, (model_id, model_name, complexity) in enumerate(models_to_test, 1):
            print(f"\n[{i}/{len(models_to_test)}] Processing {model_id}...")
            
            result = self.test_single_model(model_id, model_name, complexity)
            self.results.append(result)
            
            # Save intermediate results every 10 models
            if i % 10 == 0:
                self._save_intermediate_results()
        
        # Save final results
        self._save_final_results()
    
    def _save_intermediate_results(self):
        """Save intermediate results to JSON."""
        output_file = self.output_dir / "test_results_intermediate.json"
        
        with open(output_file, 'w') as f:
            json.dump(
                [asdict(r) for r in self.results],
                f,
                indent=2
            )
        
        print(f"\n💾 Intermediate results saved to: {output_file}")
    
    def _save_final_results(self):
        """Generate and save comprehensive test report."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Calculate statistics
        total_models = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total_models - successful
        
        parse_success = sum(1 for r in self.results if r.parse_success)
        layout_success = sum(1 for r in self.results if r.layout_generated)
        
        total_species = sum(r.species_count for r in self.results)
        total_reactions = sum(r.reactions_count for r in self.results)
        total_places = sum(r.places_created for r in self.results)
        total_transitions = sum(r.transitions_created for r in self.results)
        total_arcs = sum(r.arcs_created for r in self.results)
        total_test_arcs = sum(r.test_arcs_created for r in self.results)
        total_inhibitor_arcs = sum(r.inhibitor_arcs_created for r in self.results)
        
        models_with_kinetics = sum(1 for r in self.results if r.has_kinetics)
        total_continuous = sum(r.continuous_transitions for r in self.results)
        total_stochastic = sum(r.stochastic_transitions for r in self.results)
        
        # Generate summary report
        report = {
            "test_metadata": {
                "test_suite": "BioModels 100 SBML Import Test",
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "total_models_tested": total_models
            },
            "summary_statistics": {
                "success_rate": f"{(successful/total_models)*100:.1f}%",
                "models_successful": successful,
                "models_failed": failed,
                "parse_success_rate": f"{(parse_success/total_models)*100:.1f}%",
                "layout_success_rate": f"{(layout_success/total_models)*100:.1f}%"
            },
            "conversion_statistics": {
                "total_species": total_species,
                "total_reactions": total_reactions,
                "total_places_created": total_places,
                "total_transitions_created": total_transitions,
                "total_normal_arcs": total_arcs,
                "total_test_arcs": total_test_arcs,
                "total_inhibitor_arcs": total_inhibitor_arcs,
                "avg_species_per_model": total_species / total_models,
                "avg_reactions_per_model": total_reactions / total_models,
                "avg_places_per_model": total_places / total_models,
                "avg_transitions_per_model": total_transitions / total_models
            },
            "kinetics_statistics": {
                "models_with_kinetics": models_with_kinetics,
                "percentage_with_kinetics": f"{(models_with_kinetics/total_models)*100:.1f}%",
                "total_continuous_transitions": total_continuous,
                "total_stochastic_transitions": total_stochastic,
                "continuous_ratio": f"{(total_continuous/(total_continuous+total_stochastic))*100:.1f}%" if (total_continuous+total_stochastic) > 0 else "N/A"
            },
            "detailed_results": [asdict(r) for r in self.results]
        }
        
        # Save JSON report
        json_file = self.output_dir / "test_results_complete.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown report
        self._generate_markdown_report(report)
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"TEST SUITE COMPLETE")
        print(f"{'='*70}")
        print(f"Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        print(f"Models tested: {total_models}")
        print(f"Success rate: {(successful/total_models)*100:.1f}%")
        print(f"  ✓ Successful: {successful}")
        print(f"  ✗ Failed: {failed}")
        print(f"\nConversion statistics:")
        print(f"  Species → Places: {total_species} → {total_places}")
        print(f"  Reactions → Transitions: {total_reactions} → {total_transitions}")
        print(f"  Normal arcs: {total_arcs}")
        print(f"  Test arcs (catalysts): {total_test_arcs}")
        print(f"  Inhibitor arcs: {total_inhibitor_arcs}")
        print(f"\nKinetics:")
        print(f"  Models with kinetics: {models_with_kinetics} ({(models_with_kinetics/total_models)*100:.1f}%)")
        print(f"  Continuous transitions: {total_continuous}")
        print(f"  Stochastic transitions: {total_stochastic}")
        print(f"\nResults saved to:")
        print(f"  📄 {json_file}")
        print(f"  📄 {self.output_dir / 'test_results_report.md'}")
        print(f"{'='*70}\n")
    
    def _generate_markdown_report(self, report: Dict):
        """Generate human-readable markdown report."""
        md_file = self.output_dir / "test_results_report.md"
        
        with open(md_file, 'w') as f:
            f.write("# BioModels 100 SBML Import Test Results\n\n")
            
            # Metadata
            f.write("## Test Metadata\n\n")
            f.write(f"- **Test Suite**: {report['test_metadata']['test_suite']}\n")
            f.write(f"- **Start Time**: {report['test_metadata']['start_time']}\n")
            f.write(f"- **End Time**: {report['test_metadata']['end_time']}\n")
            f.write(f"- **Duration**: {report['test_metadata']['duration_seconds']:.1f}s "
                   f"({report['test_metadata']['duration_seconds']/60:.1f} minutes)\n")
            f.write(f"- **Models Tested**: {report['test_metadata']['total_models_tested']}\n\n")
            
            # Summary
            f.write("## Summary Statistics\n\n")
            stats = report['summary_statistics']
            f.write(f"- **Success Rate**: {stats['success_rate']}\n")
            f.write(f"- **Successful**: {stats['models_successful']}\n")
            f.write(f"- **Failed**: {stats['models_failed']}\n")
            f.write(f"- **Parse Success Rate**: {stats['parse_success_rate']}\n")
            f.write(f"- **Layout Success Rate**: {stats['layout_success_rate']}\n\n")
            
            # Conversion stats
            f.write("## Conversion Statistics\n\n")
            conv = report['conversion_statistics']
            f.write(f"- **Total Species**: {conv['total_species']}\n")
            f.write(f"- **Total Reactions**: {conv['total_reactions']}\n")
            f.write(f"- **Places Created**: {conv['total_places_created']}\n")
            f.write(f"- **Transitions Created**: {conv['total_transitions_created']}\n")
            f.write(f"- **Normal Arcs**: {conv['total_normal_arcs']}\n")
            f.write(f"- **Test Arcs (Catalysts)**: {conv['total_test_arcs']}\n")
            f.write(f"- **Inhibitor Arcs**: {conv['total_inhibitor_arcs']}\n\n")
            f.write(f"**Averages per Model:**\n")
            f.write(f"- Species: {conv['avg_species_per_model']:.1f}\n")
            f.write(f"- Reactions: {conv['avg_reactions_per_model']:.1f}\n")
            f.write(f"- Places: {conv['avg_places_per_model']:.1f}\n")
            f.write(f"- Transitions: {conv['avg_transitions_per_model']:.1f}\n\n")
            
            # Kinetics
            f.write("## Kinetics Statistics\n\n")
            kin = report['kinetics_statistics']
            f.write(f"- **Models with Kinetics**: {kin['models_with_kinetics']} ({kin['percentage_with_kinetics']})\n")
            f.write(f"- **Continuous Transitions**: {kin['total_continuous_transitions']}\n")
            f.write(f"- **Stochastic Transitions**: {kin['total_stochastic_transitions']}\n")
            f.write(f"- **Continuous Ratio**: {kin['continuous_ratio']}\n\n")
            
            # Detailed results table
            f.write("## Detailed Results\n\n")
            f.write("| # | Model ID | Name | Success | Species | Reactions | Places | Transitions | Arcs |\n")
            f.write("|---|----------|------|---------|---------|-----------|--------|-------------|------|\n")
            
            for i, result in enumerate(self.results, 1):
                status = "✅" if result.success else "❌"
                f.write(f"| {i} | {result.model_id} | {result.model_name[:40]} | {status} | "
                       f"{result.species_count} | {result.reactions_count} | {result.places_created} | "
                       f"{result.transitions_created} | {result.arcs_created + result.test_arcs_created + result.inhibitor_arcs_created} |\n")
            
            f.write("\n## Failed Models\n\n")
            failed_models = [r for r in self.results if not r.success]
            
            if failed_models:
                for result in failed_models:
                    f.write(f"### {result.model_id} - {result.model_name}\n\n")
                    f.write(f"**Errors:**\n")
                    for error in result.errors:
                        f.write(f"- {error}\n")
                    f.write("\n")
            else:
                f.write("No failed models! 🎉\n\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test Shypn SBML import with 100 BioModels',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of models to test (for quick testing)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=str(repo_root / 'doc' / 'thesis' / 'sbml_models'),
        help='Output directory for results'
    )
    
    args = parser.parse_args()
    
    # Create test suite
    suite = BioModels100TestSuite(output_dir=args.output_dir)
    
    try:
        suite.run_all_tests(limit=args.limit)
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        suite._save_intermediate_results()
        return 1
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
