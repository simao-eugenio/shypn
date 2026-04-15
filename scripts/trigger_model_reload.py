#!/usr/bin/env python3
"""Helper script to trigger cache invalidation by reloading and re-saving a model.

After editing a .shy file directly (e.g., via text replacement), run this script
to emit the 'file.saved' event and trigger cache invalidation in ModelRepository.

Usage:
    python trigger_model_reload.py <path_to_model.shy>

Example:
    python trigger_model_reload.py workspace/projects/gata/models/phase3a_spatial_clean.shy
"""

import sys
from pathlib import Path

# Add shypn to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.data.canvas.document_model import DocumentModel


def trigger_reload(model_path: str):
    """Load and re-save model to trigger EventBus notification.
    
    Args:
        model_path: Path to .shy model file
    """
    model_file = Path(model_path)
    
    if not model_file.exists():
        print(f"❌ Model file not found: {model_path}")
        return False
    
    if not model_file.suffix == '.shy':
        print(f"❌ Not a .shy file: {model_path}")
        return False
    
    print(f"📂 Loading model: {model_path}")
    try:
        # This will emit 'file.opened' event
        model = DocumentModel.load_from_file(str(model_file))
        print(f"✅ Model loaded: {model.metadata.get('name', 'unnamed')}")
        
        # Re-save to trigger 'file.saved' event
        print(f"💾 Re-saving to trigger cache invalidation...")
        model.save_to_file(str(model_file))
        print(f"✅ Model saved - EventBus.emit('file.saved') triggered")
        print(f"   → ModelRepository caches will be invalidated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    model_path = sys.argv[1]
    success = trigger_reload(model_path)
    sys.exit(0 if success else 1)
