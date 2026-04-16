"""Unit tests for SQLite compound database."""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime

from shypn.thermodynamics.database.compound_db import (
    CompoundIdentity,
    SQLiteCompoundDatabase
)


class TestCompoundIdentity(unittest.TestCase):
    """Test CompoundIdentity dataclass."""
    
    def test_basic_identity(self):
        """Test creating basic identity."""
        identity = CompoundIdentity(
            kegg_id="C00002",
            primary_name="ATP"
        )
        
        self.assertEqual(identity.kegg_id, "C00002")
        self.assertEqual(identity.primary_name, "ATP")
        self.assertEqual(identity.aliases, [])
    
    def test_all_names(self):
        """Test all_names property."""
        identity = CompoundIdentity(
            kegg_id="C00002",
            primary_name="ATP",
            aliases=["adenosine triphosphate", "Adenosine-5'-triphosphate"]
        )
        
        self.assertEqual(len(identity.all_names), 3)
        self.assertIn("ATP", identity.all_names)
        self.assertIn("adenosine triphosphate", identity.all_names)
    
    def test_has_database_id(self):
        """Test database ID checking."""
        identity = CompoundIdentity(
            kegg_id="C00002",
            chebi_id="CHEBI:15422",
            bigg_id="atp_c",
            primary_name="ATP"
        )
        
        self.assertTrue(identity.has_database_id('kegg'))
        self.assertTrue(identity.has_database_id('chebi'))
        self.assertTrue(identity.has_database_id('bigg'))
        self.assertFalse(identity.has_database_id('unknown'))


class TestSQLiteCompoundDatabase(unittest.TestCase):
    """Test SQLite compound database."""
    
    def setUp(self):
        """Create temporary database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_compounds.db"
        self.db = SQLiteCompoundDatabase(db_path=self.db_path)
    
    def tearDown(self):
        """Close database and cleanup."""
        self.db.close()
        if self.db_path.exists():
            self.db_path.unlink()
    
    def test_insert_and_retrieve(self):
        """Test basic insert and retrieval."""
        identity = CompoundIdentity(
            kegg_id="C00002",
            chebi_id="CHEBI:15422",
            primary_name="ATP",
            aliases=["adenosine triphosphate"],
            source="test"
        )
        
        # Insert
        self.assertTrue(self.db.insert(identity))
        
        # Retrieve by KEGG
        retrieved = self.db.get_by_kegg("C00002")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.primary_name, "ATP")
        self.assertIn("adenosine triphosphate", retrieved.aliases)
    
    def test_get_by_chebi(self):
        """Test retrieval by ChEBI ID."""
        identity = CompoundIdentity(
            kegg_id="C00002",
            chebi_id="CHEBI:15422",
            primary_name="ATP"
        )
        self.db.insert(identity)
        
        # Test both formats
        retrieved1 = self.db.get_by_chebi("CHEBI:15422")
        retrieved2 = self.db.get_by_chebi("15422")
        
        self.assertIsNotNone(retrieved1)
        self.assertIsNotNone(retrieved2)
        self.assertEqual(retrieved1.kegg_id, "C00002")
    
    def test_get_by_bigg(self):
        """Test retrieval by BiGG ID."""
        identity = CompoundIdentity(
            kegg_id="C00002",
            bigg_id="atp_c",
            primary_name="ATP"
        )
        self.db.insert(identity)
        
        retrieved = self.db.get_by_bigg("atp_c")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.kegg_id, "C00002")
    
    def test_get_by_name(self):
        """Test retrieval by compound name."""
        identity = CompoundIdentity(
            kegg_id="C00002",
            primary_name="ATP",
            aliases=["adenosine triphosphate"]
        )
        self.db.insert(identity)
        
        # Test primary name (case-insensitive)
        retrieved1 = self.db.get_by_name("ATP")
        retrieved2 = self.db.get_by_name("atp")
        self.assertIsNotNone(retrieved1)
        self.assertIsNotNone(retrieved2)
        
        # Test alias
        retrieved3 = self.db.get_by_name("adenosine triphosphate")
        self.assertIsNotNone(retrieved3)
    
    def test_search_by_name(self):
        """Test full-text search."""
        # Insert test data
        compounds = [
            CompoundIdentity("C00002", primary_name="ATP"),
            CompoundIdentity("C00008", primary_name="ADP"),
            CompoundIdentity("C00020", primary_name="AMP"),
            CompoundIdentity("C00031", primary_name="glucose"),
        ]
        for comp in compounds:
            self.db.insert(comp)
        
        # Search for "A*" (should match ATP, ADP, AMP)
        results = self.db.search_by_name("A*")
        self.assertGreaterEqual(len(results), 3)
        
        # Search for specific name
        results = self.db.search_by_name("glucose")
        self.assertGreaterEqual(len(results), 1)
    
    def test_update(self):
        """Test updating compound."""
        identity = CompoundIdentity(
            kegg_id="C00002",
            primary_name="ATP_old"
        )
        self.db.insert(identity)
        
        # Update
        identity.primary_name = "ATP"
        identity.chebi_id = "CHEBI:15422"
        self.assertTrue(self.db.update(identity))
        
        # Verify
        retrieved = self.db.get_by_kegg("C00002")
        self.assertEqual(retrieved.primary_name, "ATP")
        self.assertEqual(retrieved.chebi_id, "CHEBI:15422")
    
    def test_upsert(self):
        """Test upsert (insert or update)."""
        identity = CompoundIdentity(
            kegg_id="C00002",
            primary_name="ATP"
        )
        
        # First upsert (insert)
        self.assertTrue(self.db.upsert(identity))
        self.assertEqual(self.db.count(), 1)
        
        # Second upsert (update)
        identity.chebi_id = "CHEBI:15422"
        self.assertTrue(self.db.upsert(identity))
        self.assertEqual(self.db.count(), 1)
        
        # Verify update
        retrieved = self.db.get_by_kegg("C00002")
        self.assertEqual(retrieved.chebi_id, "CHEBI:15422")
    
    def test_delete(self):
        """Test deleting compound."""
        identity = CompoundIdentity(
            kegg_id="C00002",
            primary_name="ATP"
        )
        self.db.insert(identity)
        
        # Delete
        self.assertTrue(self.db.delete("C00002"))
        self.assertEqual(self.db.count(), 0)
        
        # Verify
        self.assertIsNone(self.db.get_by_kegg("C00002"))
    
    def test_get_all_kegg_ids(self):
        """Test getting all KEGG IDs."""
        compounds = [
            CompoundIdentity("C00002", primary_name="ATP"),
            CompoundIdentity("C00008", primary_name="ADP"),
            CompoundIdentity("C00020", primary_name="AMP"),
        ]
        for comp in compounds:
            self.db.insert(comp)
        
        kegg_ids = self.db.get_all_kegg_ids()
        self.assertEqual(len(kegg_ids), 3)
        self.assertIn("C00002", kegg_ids)
        self.assertIn("C00008", kegg_ids)
    
    def test_statistics(self):
        """Test database statistics."""
        # Insert test data
        self.db.insert(CompoundIdentity("C00002", primary_name="ATP", chebi_id="CHEBI:15422"))
        self.db.insert(CompoundIdentity("C00008", primary_name="ADP", bigg_id="adp_c"))
        self.db.insert(CompoundIdentity("C00020", primary_name="AMP"))
        
        stats = self.db.get_statistics()
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['with_chebi'], 1)
        self.assertEqual(stats['with_bigg'], 1)
    
    def test_duplicate_insert(self):
        """Test that duplicate inserts are rejected."""
        identity = CompoundIdentity(
            kegg_id="C00002",
            primary_name="ATP"
        )
        
        # First insert succeeds
        self.assertTrue(self.db.insert(identity))
        
        # Second insert fails
        self.assertFalse(self.db.insert(identity))
    
    def test_context_manager(self):
        """Test using database as context manager."""
        with SQLiteCompoundDatabase(db_path=self.db_path) as db:
            identity = CompoundIdentity("C00002", primary_name="ATP")
            db.insert(identity)
            self.assertEqual(db.count(), 1)


if __name__ == '__main__':
    unittest.main()
