# Metadata Management System - Usage Guide

**Location:** `src/shypn/crossfetch/metadata/`  
**Date:** October 2025  
**Status:** ✅ Complete - Core Implementation

## Overview

The metadata management system implements the **"gemini reflection"** pattern - every operation on a pathway file is automatically reflected in its corresponding metadata file. This provides complete transparency and traceability for cross-fetch enrichment operations.

## Purpose

- **Automatic Tracking**: Log all file operations (create, save, load, delete, rename, copy)
- **Enrichment History**: Record which sources enriched which fields, with quality scores
- **Transparency**: Know exactly where each piece of data came from
- **Reproducibility**: Replay enrichment process with same sources and settings
- **Quality Monitoring**: Track quality scores over time

## Architecture

```
project/
├── models/
│   └── glycolysis.shy                # Pathway file (.shy extension)
└── metadata/
    └── glycolysis.shy.meta.json      # Metadata file (automatic)
```

**Key Principle**: Every pathway file has a corresponding metadata file in the `metadata/` directory.

**File Extension**: Shypn uses `.shy` as the primary file extension (legacy `.shypn` also supported).

## Components

### 1. BaseMetadataManager (Abstract)

Base class defining the metadata interface.

**Abstract Methods**:
- `create()` - Create new metadata file
- `read()` - Read metadata from file
- `update()` - Update metadata file
- `delete()` - Delete metadata file

**Concrete Methods**:
- `exists()` - Check if metadata exists
- `log_operation()` - Log file operation
- `add_enrichment_record()` - Record enrichment
- `get_enrichment_history()` - Get enrichment history
- `get_statistics()` - Get statistics
- `get_sources_used()` - Get list of sources
- `get_quality_report()` - Get quality scores

### 2. JSONMetadataManager (Concrete)

JSON implementation with safety features.

**Features**:
- Atomic writes (write to temp, then rename)
- Automatic backups (.bak files)
- Deep merge for updates
- Pretty-printing for version control
- Error handling and logging

### 3. MetadataManagerFactory

Factory for creating appropriate managers.

**Features**:
- Auto-detect format from file extension
- Support multiple formats (JSON, XML, SQLite)
- Configuration management
- Manager class registration

### 4. FileOperationsTracker

Tracks file operations and updates metadata automatically.

**Operations Tracked**:
- `create_file()` - Create file and metadata
- `save_file()` - Log save operation
- `load_file()` - Log load operation
- `delete_file()` - Delete file and metadata
- `rename_file()` - Rename and update metadata
- `copy_file()` - Copy file and metadata

## Usage Examples

### Basic Usage

```python
from pathlib import Path
from shypn.crossfetch.metadata import create_metadata_manager

# Create metadata manager
manager = create_metadata_manager(Path("glycolysis.shy"))

# Create metadata file
manager.create()

# Add enrichment record
manager.add_enrichment_record(
    data_type="coordinates",
    source="KEGG",
    quality_score=0.85,
    fields_enriched=["species[0].x", "species[0].y"],
    details={"pathway_id": "hsa00010"}
)

# Log operation
manager.log_operation("save", {"user": "simao", "changes": "Added enzymes"})

# Get enrichment history
history = manager.get_enrichment_history()
print(f"Total enrichments: {len(history)}")

# Get statistics
stats = manager.get_statistics()
print(f"Sources used: {stats['sources_used']}")
print(f"Quality scores: {stats['quality_scores']}")
```

### File Operations Tracking

```python
from shypn.crossfetch.metadata import FileOperationsTracker

# Create tracker
tracker = FileOperationsTracker()

# Create file with metadata
tracker.create_file(
    Path("glycolysis.shy"),
    user="simao",
    initial_data={"project": "metabolic_pathways"}
)

# Log save operation
tracker.save_file(
    Path("glycolysis.shy"),
    user="simao",
    changes={"added": ["PFK", "GAPDH"], "modified": ["HK"]}
)

# Log load operation
tracker.load_file(Path("glycolysis.shy"), user="maria")

# Rename file
tracker.rename_file(
    Path("glycolysis.shy"),
    Path("glycolysis_v2.shy"),
    user="simao"
)

# Copy file
tracker.copy_file(
    Path("glycolysis_v2.shy"),
    Path("glycolysis_backup.shy"),
    user="simao",
    copy_metadata=True
)

# Delete file
tracker.delete_file(
    Path("glycolysis_backup.shy"),
    user="simao",
    delete_metadata=True  # Also delete metadata
)
```

### Enrichment Workflow

```python
from shypn.crossfetch.metadata import create_metadata_manager

# Create manager
manager = create_metadata_manager(Path("glycolysis.shy"))

# Ensure metadata exists
if not manager.exists():
    manager.create()

# Record multiple enrichments
enrichments = [
    {
        "data_type": "coordinates",
        "source": "KEGG",
        "quality_score": 0.85,
        "fields_enriched": ["species[0].x", "species[0].y"]
    },
    {
        "data_type": "concentrations",
        "source": "BioModels",
        "quality_score": 0.95,
        "fields_enriched": ["species[0].initial_concentration"]
    },
    {
        "data_type": "kinetics",
        "source": "SABIO-RK",
        "quality_score": 0.90,
        "fields_enriched": ["reactions[0].kinetic_law"]
    }
]

for enrichment in enrichments:
    manager.add_enrichment_record(**enrichment)

# Get enrichment history by type
coords_history = manager.get_enrichment_history(data_type="coordinates")
print(f"Coordinates enriched {len(coords_history)} times")

# Get quality report
quality = manager.get_quality_report()
for data_type, score in quality.items():
    print(f"{data_type}: {score:.2f}")

# Get sources used
sources = manager.get_sources_used()
print(f"Data from: {', '.join(sources)}")
```

### Factory Pattern

```python
from shypn.crossfetch.metadata import (
    MetadataManagerFactory,
    MetadataFormat
)

# Auto-detect format from extension
manager = MetadataManagerFactory.create(Path("glycolysis.shy"))
# Creates JSONMetadataManager (default for .shy files)

# Explicit format
manager = MetadataManagerFactory.create(
    Path("model.sbml"),
    format=MetadataFormat.XML
)

# Check supported formats
formats = MetadataManagerFactory.get_supported_formats()
print(f"Supported: {[f.value for f in formats]}")

# Register custom manager
from my_module import CustomMetadataManager
MetadataManagerFactory.register_manager(
    MetadataFormat.SQLITE,
    CustomMetadataManager
)

# Set default format
MetadataManagerFactory.set_default_format(MetadataFormat.JSON)

# Set extension preference
MetadataManagerFactory.set_extension_preference(
    ".shy",
    MetadataFormat.JSON
)
```

### Verification and Repair

```python
from shypn.crossfetch.metadata import FileOperationsTracker

tracker = FileOperationsTracker()

# Verify metadata is in sync
is_sync = tracker.verify_metadata_sync(Path("glycolysis.shy"))
if not is_sync:
    print("Metadata out of sync!")
    
    # Repair metadata
    if tracker.repair_metadata(Path("glycolysis.shy")):
        print("Metadata repaired successfully")
```

## Metadata File Format

```json
{
  "pathway_file": "glycolysis.shy",
  "created": "2025-01-10T14:23:15Z",
  "created_by": "simao",
  "last_modified": "2025-01-10T14:30:22Z",
  "version": "1.0",
  
  "enrichments": [
    {
      "data_type": "coordinates",
      "source": "KEGG",
      "quality_score": 0.85,
      "fields_enriched": ["species[0].x", "species[0].y"],
      "timestamp": "2025-01-10T14:23:20Z",
      "details": {
        "pathway_id": "hsa00010",
        "confidence": "high"
      }
    },
    {
      "data_type": "concentrations",
      "source": "BioModels",
      "quality_score": 0.95,
      "fields_enriched": ["species[0].initial_concentration"],
      "timestamp": "2025-01-10T14:25:30Z",
      "details": {
        "model_id": "BIOMD0000000001"
      }
    }
  ],
  
  "operations": [
    {
      "operation": "create",
      "timestamp": "2025-01-10T14:23:15Z",
      "details": {
        "user": "simao",
        "file_path": "/project/models/glycolysis.shy"
      }
    },
    {
      "operation": "save",
      "timestamp": "2025-01-10T14:30:22Z",
      "details": {
        "user": "simao",
        "changes": {"added": ["PFK"], "modified": ["HK"]},
        "file_size": 45678
      }
    }
  ],
  
  "statistics": {
    "total_enrichments": 2,
    "sources_used": ["KEGG", "BioModels"],
    "quality_scores": {
      "coordinates": 0.85,
      "concentrations": 0.95
    }
  }
}
```

## Integration with File Loaders

### PersistencyManager Integration

```python
from shypn.crossfetch.metadata import FileOperationsTracker

class PersistencyManager:
    """Pathway file persistency with automatic metadata tracking."""
    
    def __init__(self):
        self.tracker = FileOperationsTracker()
    
    def save_pathway(self, pathway, file_path, user=None):
        """Save pathway with metadata tracking."""
        # Save pathway file
        # ... existing save logic ...
        
        # Track operation in metadata
        self.tracker.save_file(file_path, user=user)
    
    def load_pathway(self, file_path, user=None):
        """Load pathway with metadata tracking."""
        # Load pathway file
        # ... existing load logic ...
        
        # Track operation in metadata
        self.tracker.load_file(file_path, user=user)
        
        return pathway
    
    def delete_pathway(self, file_path, user=None):
        """Delete pathway with metadata tracking."""
        # Delete pathway file
        # ... existing delete logic ...
        
        # Track operation in metadata
        self.tracker.delete_file(file_path, user=user)
```

## Best Practices

### 1. Always Create Metadata on File Creation

```python
# ❌ BAD: Create file without metadata
pathway_file.write_text(data)

# ✅ GOOD: Use tracker to create file with metadata
tracker.create_file(pathway_file, user="simao")
```

### 2. Log All Operations

```python
# ❌ BAD: Save without logging
pathway.save(file_path)

# ✅ GOOD: Save and log operation
pathway.save(file_path)
tracker.save_file(file_path, user="simao", changes={"modified": ["species"]})
```

### 3. Record Enrichments Immediately

```python
# ❌ BAD: Enrich data without recording
species.x = kegg_data["x"]
species.y = kegg_data["y"]

# ✅ GOOD: Enrich and record immediately
species.x = kegg_data["x"]
species.y = kegg_data["y"]
manager.add_enrichment_record(
    data_type="coordinates",
    source="KEGG",
    quality_score=0.85,
    fields_enriched=["species[0].x", "species[0].y"]
)
```

### 4. Verify Metadata Sync Periodically

```python
# Periodic verification
if not tracker.verify_metadata_sync(pathway_file):
    logger.warning(f"Metadata out of sync for {pathway_file.name}")
    tracker.repair_metadata(pathway_file)
```

### 5. Include Meaningful Details

```python
# ❌ BAD: Minimal details
manager.add_enrichment_record("coordinates", "KEGG", 0.85, ["x", "y"])

# ✅ GOOD: Rich details
manager.add_enrichment_record(
    data_type="coordinates",
    source="KEGG",
    quality_score=0.85,
    fields_enriched=["species[0].x", "species[0].y"],
    details={
        "pathway_id": "hsa00010",
        "organism": "Homo sapiens",
        "confidence": "high",
        "method": "manual_curation"
    }
)
```

## API Reference

### BaseMetadataManager

```python
class BaseMetadataManager(ABC):
    """Abstract base for metadata management."""
    
    def __init__(self, pathway_file: Path)
    
    # Abstract methods (must implement)
    @abstractmethod
    def create(self, initial_data: Optional[Dict] = None) -> bool
    @abstractmethod
    def read(self) -> Optional[Dict[str, Any]]
    @abstractmethod
    def update(self, data: Dict[str, Any]) -> bool
    @abstractmethod
    def delete(self) -> bool
    
    # Concrete methods (shared implementation)
    def exists(self) -> bool
    def log_operation(self, operation: str, details: Optional[Dict] = None)
    def add_enrichment_record(self, data_type, source, quality_score, 
                             fields_enriched, details=None)
    def get_enrichment_history(self, data_type: Optional[str] = None) -> List[Dict]
    def get_statistics(self) -> Dict[str, Any]
    def get_sources_used(self) -> List[str]
    def get_quality_report(self) -> Dict[str, float]
    def get_path(self) -> Path
```

### JSONMetadataManager

```python
class JSONMetadataManager(BaseMetadataManager):
    """JSON implementation with safety features."""
    
    def __init__(self, pathway_file: Path, pretty_print=True, indent=2)
    
    # Implements abstract methods
    def create(self, initial_data: Optional[Dict] = None) -> bool
    def read(self) -> Optional[Dict[str, Any]]
    def update(self, data: Dict[str, Any]) -> bool
    def delete(self) -> bool
    
    # Additional features
    def restore_from_backup(self) -> bool
    def export_to_dict(self) -> Optional[Dict[str, Any]]
    def import_from_dict(self, data: Dict[str, Any]) -> bool
```

### FileOperationsTracker

```python
class FileOperationsTracker:
    """Tracks file operations and updates metadata."""
    
    def __init__(self, metadata_manager_class=JSONMetadataManager)
    
    def create_file(self, file_path: Path, initial_data: Optional[Dict] = None,
                   user: Optional[str] = None) -> bool
    def save_file(self, file_path: Path, user: Optional[str] = None,
                 changes: Optional[Dict] = None) -> bool
    def load_file(self, file_path: Path, user: Optional[str] = None) -> bool
    def delete_file(self, file_path: Path, user: Optional[str] = None,
                   delete_metadata: bool = True) -> bool
    def rename_file(self, old_path: Path, new_path: Path,
                   user: Optional[str] = None) -> bool
    def copy_file(self, source_path: Path, dest_path: Path,
                 user: Optional[str] = None, copy_metadata: bool = True) -> bool
    
    def get_metadata_manager(self, file_path: Path) -> BaseMetadataManager
    def verify_metadata_sync(self, file_path: Path) -> bool
    def repair_metadata(self, file_path: Path) -> bool
```

### MetadataManagerFactory

```python
class MetadataManagerFactory:
    """Factory for creating metadata managers."""
    
    @classmethod
    def create(cls, pathway_file: Path, format: Optional[MetadataFormat] = None,
              **kwargs) -> BaseMetadataManager
    
    @classmethod
    def register_manager(cls, format: MetadataFormat, 
                        manager_class: Type[BaseMetadataManager])
    
    @classmethod
    def set_default_format(cls, format: MetadataFormat)
    
    @classmethod
    def get_default_format(cls) -> MetadataFormat
    
    @classmethod
    def set_extension_preference(cls, extension: str, format: MetadataFormat)
    
    @classmethod
    def get_supported_formats(cls) -> List[MetadataFormat]
    
    @classmethod
    def is_format_supported(cls, format: MetadataFormat) -> bool

# Convenience functions
def create_metadata_manager(pathway_file: Path, 
                           format: Optional[MetadataFormat] = None,
                           **kwargs) -> BaseMetadataManager

def create_json_manager(pathway_file: Path, **kwargs) -> JSONMetadataManager
```

## Status

✅ **Complete**: Core metadata management system
- BaseMetadataManager (abstract base)
- JSONMetadataManager (JSON implementation)
- MetadataManagerFactory (factory pattern)
- FileOperationsTracker (automatic reflection)

⚠️ **Pending**:
- XMLMetadataManager (for SBML compatibility)
- SQLiteMetadataManager (for large projects)
- Integration with PersistencyManager
- Unit tests
- Integration tests

## Next Steps

1. **Integration**: Connect to file loaders (PersistencyManager)
2. **Testing**: Create comprehensive test suite
3. **Additional Managers**: Implement XML and SQLite managers
4. **Documentation**: Add integration guide
5. **Examples**: Create real-world usage examples

---

**Author**: Shypn Development Team  
**Date**: October 2025  
**Version**: 1.0.0
