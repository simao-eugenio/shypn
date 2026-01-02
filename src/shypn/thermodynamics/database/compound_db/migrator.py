"""Migrator for converting JSON data to SQLite compound database.

Provides tools to import compound data from various sources:
- JSON mapping files (compound_mappings.json, xref data)
- KEGG API (auto-populate during enrichment)
- Manual additions
"""

import json
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from .base import CompoundIdentity
from .sqlite_db import SQLiteCompoundDatabase


class CompoundDatabaseMigrator:
    """Migrate compound data from JSON to SQLite.
    
    Supports multiple data sources:
    - compound_mappings.json (thermodynamics data)
    - xref JSON files (ChEBI/BiGG mappings)
    - Custom JSON format
    
    Example:
        >>> migrator = CompoundDatabaseMigrator(db)
        >>> migrator.import_from_compound_mappings('compound_mappings.json')
        >>> migrator.import_from_xref_json('kegg_to_chebi.json')
    """
    
    def __init__(self, database: SQLiteCompoundDatabase):
        """Initialize migrator.
        
        Args:
            database: Target SQLite database
        """
        self.db = database
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def import_from_compound_mappings(self, json_path: Path) -> int:
        """Import from compound_mappings.json format.
        
        Format:
        {
          "compounds": {
            "C00002": {
              "kegg_id": "C00002",
              "chebi_id": "CHEBI:15422",
              "names": ["ATP", "adenosine triphosphate", ...]
            }
          }
        }
        
        Args:
            json_path: Path to compound_mappings.json
            
        Returns:
            Number of compounds imported
        """
        self.logger.info(f"Importing from {json_path}")
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        compounds = data.get('compounds', {})
        imported = 0
        
        for kegg_id, info in compounds.items():
            names = info.get('names', [])
            primary_name = names[0] if names else kegg_id
            aliases = names[1:] if len(names) > 1 else []
            
            identity = CompoundIdentity(
                kegg_id=kegg_id,
                chebi_id=info.get('chebi_id'),
                bigg_id=None,  # Not in compound_mappings.json
                primary_name=primary_name,
                aliases=aliases,
                formula=None,  # Not in compound_mappings.json
                source='compound_mappings_json',
                last_updated=datetime.now()
            )
            
            if self.db.upsert(identity):
                imported += 1
        
        self.logger.info(f"Imported {imported} compounds from compound_mappings.json")
        return imported
    
    def import_from_kegg_to_chebi(self, json_path: Path) -> int:
        """Import from kegg_to_chebi.json format.
        
        Format:
        {
          "C00002": "CHEBI:15422",
          "C00008": "CHEBI:16761",
          ...
        }
        
        Args:
            json_path: Path to kegg_to_chebi.json
            
        Returns:
            Number of mappings imported
        """
        self.logger.info(f"Importing from {json_path}")
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        imported = 0
        for kegg_id, chebi_id in data.items():
            # Skip metadata keys
            if kegg_id.startswith('_'):
                continue
            
            # Check if exists, update or create
            existing = self.db.get_by_kegg(kegg_id)
            if existing:
                existing.chebi_id = chebi_id
                existing.source = 'xref_json_update'
                self.db.update(existing)
            else:
                identity = CompoundIdentity(
                    kegg_id=kegg_id,
                    chebi_id=chebi_id,
                    primary_name=kegg_id,  # Will be updated later
                    source='xref_json',
                    last_updated=datetime.now()
                )
                self.db.insert(identity)
            
            imported += 1
        
        self.logger.info(f"Imported {imported} ChEBI mappings")
        return imported
    
    def import_from_bigg_to_kegg(self, json_path: Path) -> int:
        """Import from bigg_to_kegg.json format.
        
        Format:
        {
          "atp_c": "C00002",
          "adp_c": "C00008",
          ...
        }
        
        Args:
            json_path: Path to bigg_to_kegg.json
            
        Returns:
            Number of mappings imported
        """
        self.logger.info(f"Importing from {json_path}")
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        imported = 0
        for bigg_id, kegg_id in data.items():
            # Skip metadata keys
            if bigg_id.startswith('_'):
                continue
            
            # Check if exists, update or create
            existing = self.db.get_by_kegg(kegg_id)
            if existing:
                existing.bigg_id = bigg_id
                existing.source = 'xref_json_update'
                self.db.update(existing)
            else:
                identity = CompoundIdentity(
                    kegg_id=kegg_id,
                    bigg_id=bigg_id,
                    primary_name=kegg_id,  # Will be updated later
                    source='xref_json',
                    last_updated=datetime.now()
                )
                self.db.insert(identity)
            
            imported += 1
        
        self.logger.info(f"Imported {imported} BiGG mappings")
        return imported
    
    def import_from_compound_aliases(self, json_path: Path) -> int:
        """Import from compound_aliases.json format.
        
        Format:
        {
          "ATP": "C00002",
          "adenosine triphosphate": "C00002",
          ...
        }
        
        Args:
            json_path: Path to compound_aliases.json
            
        Returns:
            Number of aliases imported
        """
        self.logger.info(f"Importing from {json_path}")
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Group aliases by KEGG ID
        kegg_aliases: Dict[str, List[str]] = {}
        for alias, kegg_id in data.items():
            # Skip metadata keys
            if alias.startswith('_'):
                continue
            
            if kegg_id not in kegg_aliases:
                kegg_aliases[kegg_id] = []
            kegg_aliases[kegg_id].append(alias)
        
        imported = 0
        for kegg_id, aliases in kegg_aliases.items():
            existing = self.db.get_by_kegg(kegg_id)
            if existing:
                # Merge aliases (avoid duplicates)
                existing_aliases = set(existing.aliases)
                new_aliases = existing_aliases.union(aliases)
                existing.aliases = list(new_aliases)
                existing.source = 'alias_json_update'
                self.db.update(existing)
            else:
                # Create new entry with first alias as primary name
                identity = CompoundIdentity(
                    kegg_id=kegg_id,
                    primary_name=aliases[0],
                    aliases=aliases[1:] if len(aliases) > 1 else [],
                    source='alias_json',
                    last_updated=datetime.now()
                )
                self.db.insert(identity)
            
            imported += 1
        
        self.logger.info(f"Imported {imported} alias groups")
        return imported
    
    def import_all_from_directory(self, data_dir: Path) -> Dict[str, int]:
        """Import all JSON files from xref data directory.
        
        Args:
            data_dir: Directory containing JSON mapping files
            
        Returns:
            Dictionary with counts per file
        """
        results = {}
        
        # Import in order
        files = [
            ('kegg_to_chebi.json', self.import_from_kegg_to_chebi),
            ('bigg_to_kegg.json', self.import_from_bigg_to_kegg),
            ('compound_aliases.json', self.import_from_compound_aliases),
        ]
        
        for filename, import_func in files:
            file_path = data_dir / filename
            if file_path.exists():
                try:
                    count = import_func(file_path)
                    results[filename] = count
                except Exception as e:
                    self.logger.error(f"Failed to import {filename}: {e}")
                    results[filename] = 0
            else:
                self.logger.warning(f"File not found: {file_path}")
                results[filename] = 0
        
        return results
