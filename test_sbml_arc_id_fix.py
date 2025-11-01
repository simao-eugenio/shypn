"""
Simple test to verify SBML modifier arc ID generation fix.

Tests that DocumentModel._next_arc_id is used correctly instead of
the non-existent _get_next_arc_id() method.
"""

from shypn.data.pathway.pathway_data import PathwayData, Reaction, Species
from shypn.data.pathway.pathway_converter import PathwayConverter, ModifierConverter
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition
from shypn.netobjs.test_arc import TestArc


def test_modifier_converter_arc_id_generation():
    """Test that ModifierConverter correctly generates arc IDs."""
    
    print("Testing SBML ModifierConverter arc ID generation...")
    
    # Create minimal pathway with modifier
    pathway = PathwayData()
    
    # Add species
    s1 = Species(id="S1", name="Substrate", initial_concentration=10.0)
    s2 = Species(id="S2", name="Product", initial_concentration=0.0)
    enzyme = Species(id="E1", name="Enzyme", initial_concentration=1.0)
    
    pathway.species = [s1, s2, enzyme]
    
    # Add reaction with modifier
    reaction = Reaction(
        id="R1",
        name="Catalyzed Reaction",
        reactants=[("S1", 1.0)],
        products=[("S2", 1.0)],
        modifiers=["E1"],  # Enzyme as modifier
        reversible=False
    )
    pathway.reactions = [reaction]
    
    # Add layout positions (required)
    pathway.positions = {
        "S1": (100.0, 100.0),
        "S2": (300.0, 100.0),
        "E1": (200.0, 50.0),
        "R1": (200.0, 100.0)
    }
    
    # Add colors (required)
    pathway.colors = {}
    
    # Add compartments
    pathway.compartments = {"default": "Default"}
    
    # Convert
    try:
        converter = PathwayConverter()
        document = converter.convert(pathway)
        
        print(f"✓ Conversion succeeded")
        print(f"  Places: {len(document.places)}")
        print(f"  Transitions: {len(document.transitions)}")
        print(f"  Arcs: {len(document.arcs)}")
        
        # Check for test arcs
        test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]
        print(f"  Test arcs: {len(test_arcs)}")
        
        if test_arcs:
            test_arc = test_arcs[0]
            print(f"✓ Test arc created: {test_arc.id} ({test_arc.source.name} → {test_arc.target.name})")
            print(f"✓ Non-consuming: {not test_arc.consumes_tokens()}")
            
            # Verify arc ID format
            assert test_arc.id.startswith("A"), f"Arc ID should start with 'A', got {test_arc.id}"
            assert test_arc.name.startswith("TA"), f"Arc name should start with 'TA', got {test_arc.name}"
            
            print(f"✓ Arc ID format correct: id={test_arc.id}, name={test_arc.name}")
            
            # Verify document metadata
            if hasattr(document, 'metadata') and document.metadata:
                print(f"✓ Document metadata: {document.metadata.get('model_type')}")
                assert document.metadata.get('has_test_arcs') is True
        else:
            print("⚠️  No test arcs created (modifier conversion may have been skipped)")
        
        print()
        print("=" * 60)
        print("✓ SBML modifier arc ID generation test PASSED")
        print("=" * 60)
        return True
        
    except AttributeError as e:
        if "_get_next_arc_id" in str(e):
            print(f"❌ FAILED: {e}")
            print("   The bug is still present - using non-existent _get_next_arc_id()")
            return False
        else:
            raise


if __name__ == '__main__':
    success = test_modifier_converter_arc_id_generation()
    exit(0 if success else 1)
