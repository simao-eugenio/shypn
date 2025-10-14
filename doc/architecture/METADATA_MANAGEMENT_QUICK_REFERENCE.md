# Metadata Management - Quick Reference

**Package**: `src/shypn/crossfetch/metadata/`  
**Pattern**: Gemini Reflection (file operations automatically reflected in metadata)

## Quick Start

```python
from pathlib import Path
from shypn.crossfetch.metadata import (
    create_metadata_manager,
    FileOperationsTracker
)

# Create manager
manager = create_metadata_manager(Path("glycolysis.shy"))

# Create tracker
tracker = FileOperationsTracker()
```

## Common Operations

### Create File with Metadata

```python
tracker.create_file(Path("pathway.shy"), user="simao")
```

### Log Save Operation

```python
tracker.save_file(Path("pathway.shy"), user="simao", 
                 changes={"added": ["enzyme1"]})
```

### Add Enrichment Record

```python
manager.add_enrichment_record(
    data_type="coordinates",
    source="KEGG",
    quality_score=0.85,
    fields_enriched=["species[0].x", "species[0].y"]
)
```

### Get Enrichment History

```python
# All enrichments
history = manager.get_enrichment_history()

# By data type
coords = manager.get_enrichment_history(data_type="coordinates")
```

### Get Statistics

```python
stats = manager.get_statistics()
# Returns: {
#   "total_enrichments": 5,
#   "sources_used": ["KEGG", "BioModels"],
#   "quality_scores": {"coordinates": 0.85, "concentrations": 0.95}
# }
```

### Rename File

```python
tracker.rename_file(
    Path("old.shy"),
    Path("new.shy"),
    user="simao"
)
```

### Copy File

```python
tracker.copy_file(
    Path("source.shy"),
    Path("destination.shy"),
    user="simao",
    copy_metadata=True
)
```

### Delete File

```python
tracker.delete_file(
    Path("pathway.shy"),
    user="simao",
    delete_metadata=True
)
```

## Metadata File Location

```
project/
├── models/
│   └── glycolysis.shy                # Your pathway file (.shy extension)
└── metadata/
    └── glycolysis.shy.meta.json      # Metadata (automatic)
```

## Metadata Structure

```json
{
  "pathway_file": "glycolysis.shy",
  "created": "2025-01-10T14:23:15Z",
  "enrichments": [
    {
      "data_type": "coordinates",
      "source": "KEGG",
      "quality_score": 0.85,
      "fields_enriched": ["species[0].x"],
      "timestamp": "2025-01-10T14:23:20Z"
    }
  ],
  "operations": [
    {
      "operation": "save",
      "timestamp": "2025-01-10T14:30:22Z",
      "details": {"user": "simao"}
    }
  ],
  "statistics": {
    "total_enrichments": 1,
    "sources_used": ["KEGG"],
    "quality_scores": {"coordinates": 0.85}
  }
}
```

## API Overview

### Managers

| Class | Purpose |
|-------|---------|
| `BaseMetadataManager` | Abstract base class |
| `JSONMetadataManager` | JSON implementation (default) |

### Factory

| Function | Purpose |
|----------|---------|
| `create_metadata_manager(path)` | Create manager (auto-detect format) |
| `create_json_manager(path)` | Create JSON manager |

### Tracker

| Method | Purpose |
|--------|---------|
| `create_file(path, user)` | Create file + metadata |
| `save_file(path, user, changes)` | Log save operation |
| `load_file(path, user)` | Log load operation |
| `delete_file(path, user)` | Delete file + metadata |
| `rename_file(old, new, user)` | Rename + update metadata |
| `copy_file(src, dst, user)` | Copy file + metadata |

### Manager Methods

| Method | Returns |
|--------|---------|
| `create(data)` | `bool` - Success |
| `read()` | `Dict` - Metadata |
| `update(data)` | `bool` - Success |
| `delete()` | `bool` - Success |
| `exists()` | `bool` - File exists |
| `log_operation(op, details)` | None |
| `add_enrichment_record(...)` | None |
| `get_enrichment_history(type)` | `List[Dict]` |
| `get_statistics()` | `Dict` |
| `get_sources_used()` | `List[str]` |
| `get_quality_report()` | `Dict[str, float]` |

## Best Practices

✅ **DO**:
- Use `FileOperationsTracker` for all file operations
- Record enrichments immediately after applying
- Include detailed information in enrichment records
- Verify metadata sync periodically

❌ **DON'T**:
- Modify files without logging operations
- Delete metadata files manually
- Skip enrichment recording
- Edit metadata files directly

## Integration Pattern

```python
class PersistencyManager:
    """Pathway file loader with automatic metadata."""
    
    def __init__(self):
        self.tracker = FileOperationsTracker()
    
    def save_pathway(self, pathway, file_path, user=None):
        # Save pathway
        pathway.save(file_path)
        
        # Track in metadata
        self.tracker.save_file(file_path, user=user)
    
    def load_pathway(self, file_path, user=None):
        # Load pathway
        pathway = Pathway.load(file_path)
        
        # Track in metadata
        self.tracker.load_file(file_path, user=user)
        
        return pathway
```

## Enrichment Recording Pattern

```python
# After enriching data from source
manager = create_metadata_manager(pathway_file)

# Record what was enriched
manager.add_enrichment_record(
    data_type="coordinates",        # What type of data
    source="KEGG",                  # Where it came from
    quality_score=0.85,             # Quality (0.0-1.0)
    fields_enriched=[               # Which fields changed
        "species[0].x",
        "species[0].y"
    ],
    details={                       # Additional context
        "pathway_id": "hsa00010",
        "confidence": "high"
    }
)
```

## Troubleshooting

### Metadata Missing

```python
# Check if exists
if not manager.exists():
    # Create it
    manager.create()
```

### Metadata Out of Sync

```python
# Verify sync
if not tracker.verify_metadata_sync(pathway_file):
    # Repair it
    tracker.repair_metadata(pathway_file)
```

### Read Errors

```python
# Read with error handling
metadata = manager.read()
if metadata is None:
    logger.error("Failed to read metadata")
    # Try repair
    manager.create()
```

## Status

✅ **Implemented**:
- Base classes (abstract + concrete)
- JSON implementation
- Factory pattern
- File operations tracker
- Usage documentation

⚠️ **Pending**:
- XML manager (SBML)
- SQLite manager (large projects)
- PersistencyManager integration
- Unit tests

---

**Quick Reference Version**: 1.0.0  
**Last Updated**: October 2025
