#!/usr/bin/env python3
"""SQLite database for heuristic parameter caching and learning.

This module implements a local database for:
1. Caching inferred kinetic parameters
2. Tracking user selections and preferences
3. Learning from usage patterns
4. Organism compatibility data
5. Fast query performance (no repeated API calls)

Database Schema:
- transition_parameters: Cached parameter values with metadata
- pathway_enrichments: Track which parameters were applied where
- heuristic_cache: Query result cache for instant lookups
- organism_compatibility: Cross-species scaling factors
"""

import sqlite3
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager


class HeuristicDatabase:
    """SQLite database manager for heuristic parameters.
    
    Features:
    - Thread-safe connection management
    - Automatic schema creation/migration
    - Type-aware parameter storage (JSON blobs)
    - Usage tracking and learning
    - Query caching for performance
    - Phase 3: Pattern learning from enrichment history
    
    Attributes:
        db_path: Path to SQLite database file
        logger: Logger instance
    """
    
    # Database version for schema migrations
    SCHEMA_VERSION = 3
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default
                    location: ~/.shypn/heuristic_parameters.db
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Determine database path
        if db_path is None:
            # Use XDG_DATA_HOME if available, otherwise ~/.shypn
            data_home = os.environ.get('XDG_DATA_HOME')
            if data_home:
                base_dir = Path(data_home) / 'shypn'
            else:
                base_dir = Path.home() / '.shypn'
            
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / 'heuristic_parameters.db')
        else:
            self.db_path = db_path
        
        self.logger.info(f"Using database: {self.db_path}")
        
        # Initialize database schema
        self._init_schema()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_schema(self):
        """Initialize database schema if not exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if we need to create schema
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_version'
            """)
            
            if not cursor.fetchone():
                self.logger.info("Creating database schema...")
                self._create_schema(conn)
            else:
                # Check version and migrate if needed
                cursor.execute("SELECT version FROM schema_version")
                version = cursor.fetchone()[0]
                if version < self.SCHEMA_VERSION:
                    self.logger.info(f"Migrating schema from v{version} to v{self.SCHEMA_VERSION}")
                    self._migrate_schema(conn, version)
    
    def _create_schema(self, conn: sqlite3.Connection):
        """Create database schema.
        
        Args:
            conn: Database connection
        """
        cursor = conn.cursor()
        
        # Table 1: Transition Parameters (Type-Aware)
        cursor.execute("""
            CREATE TABLE transition_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- Transition Type Classification
                transition_type TEXT NOT NULL 
                    CHECK(transition_type IN ('immediate', 'timed', 'stochastic', 'continuous')),
                biological_semantics TEXT,
                
                -- Universal Identifiers
                ec_number TEXT,
                enzyme_name TEXT,
                reaction_id TEXT,
                organism TEXT NOT NULL,
                
                -- Type-Specific Parameters (JSON for flexibility)
                parameters TEXT NOT NULL,  -- JSON blob
                /*
                For immediate:   {"priority": 50, "weight": 1.0}
                For timed:       {"delay": 5.0, "time_unit": "minutes"}
                For stochastic:  {"lambda": 0.05, "k_forward": 0.05, "k_reverse": 0.01}
                For continuous:  {"vmax": 226.0, "km": 0.1, "kcat": 1500, "ki": null}
                */
                
                -- Experimental Conditions
                temperature REAL,
                ph REAL,
                
                -- Source & Confidence
                source TEXT NOT NULL,
                source_id TEXT,
                pubmed_id TEXT,
                confidence_score REAL NOT NULL CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
                
                -- Usage Tracking
                import_date TEXT NOT NULL,  -- ISO8601 timestamp
                last_used TEXT,             -- ISO8601 timestamp
                usage_count INTEGER DEFAULT 0,
                user_rating INTEGER CHECK(user_rating >= -1 AND user_rating <= 1),
                notes TEXT,
                
                -- Phase 2: Undo Support
                undone INTEGER DEFAULT 0,   -- Boolean: 0=active, 1=undone
                undo_timestamp TEXT         -- ISO8601 timestamp when undone
            )
        """)
        
        # Indexes for fast queries
        cursor.execute("""
            CREATE INDEX idx_type_ec 
            ON transition_parameters(transition_type, ec_number)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_ec_organism 
            ON transition_parameters(ec_number, organism)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_type_confidence 
            ON transition_parameters(transition_type, confidence_score DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_reaction_organism
            ON transition_parameters(reaction_id, organism)
        """)
        
        # Table 2: Pathway Enrichments (Track Applications)
        cursor.execute("""
            CREATE TABLE pathway_enrichments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pathway_id TEXT,
                pathway_name TEXT,
                reaction_id TEXT,
                transition_id TEXT,
                parameter_id INTEGER NOT NULL,
                applied_date TEXT NOT NULL,  -- ISO8601 timestamp
                project_path TEXT,
                FOREIGN KEY (parameter_id) REFERENCES transition_parameters(id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX idx_pathway_enrichments
            ON pathway_enrichments(pathway_id, parameter_id)
        """)
        
        # Table 3: Heuristic Cache (Query Results)
        cursor.execute("""
            CREATE TABLE heuristic_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_key TEXT UNIQUE NOT NULL,
                recommended_parameter_id INTEGER,
                alternatives TEXT,  -- JSON array of parameter IDs
                confidence_score REAL,
                last_updated TEXT NOT NULL,  -- ISO8601 timestamp
                hit_count INTEGER DEFAULT 0,
                FOREIGN KEY (recommended_parameter_id) REFERENCES transition_parameters(id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX idx_cache_key
            ON heuristic_cache(query_key)
        """)
        
        # Table 4: Organism Compatibility
        cursor.execute("""
            CREATE TABLE organism_compatibility (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_organism TEXT NOT NULL,
                target_organism TEXT NOT NULL,
                enzyme_class TEXT,
                compatibility_score REAL NOT NULL 
                    CHECK(compatibility_score >= 0.0 AND compatibility_score <= 1.0),
                notes TEXT,
                UNIQUE(source_organism, target_organism, enzyme_class)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX idx_organism_compat
            ON organism_compatibility(source_organism, target_organism)
        """)
        
        # Table 5: BRENDA Raw Data Cache
        cursor.execute("""
            CREATE TABLE brenda_raw_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ec_number TEXT NOT NULL,
                parameter_type TEXT NOT NULL CHECK(parameter_type IN ('Km', 'Kcat', 'Ki', 'Vmax')),
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                substrate TEXT,
                organism TEXT,
                literature TEXT,
                commentary TEXT,
                query_date TEXT NOT NULL,  -- ISO8601 timestamp when fetched
                source_quality REAL,  -- Quality score 0.0-1.0 from BRENDADataFilter
                
                -- Prevent duplicate entries
                UNIQUE(ec_number, parameter_type, substrate, organism, value, literature)
            )
        """)
        
        # Indexes for BRENDA data
        cursor.execute("""
            CREATE INDEX idx_brenda_ec
            ON brenda_raw_data(ec_number, parameter_type)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_brenda_organism
            ON brenda_raw_data(ec_number, organism)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_brenda_quality
            ON brenda_raw_data(ec_number, source_quality DESC)
        """)
        
        # Table 6: BRENDA Statistics Cache (Aggregated)
        cursor.execute("""
            CREATE TABLE brenda_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ec_number TEXT NOT NULL,
                parameter_type TEXT NOT NULL,
                organism TEXT,  -- NULL means all organisms
                substrate TEXT,  -- NULL means all substrates
                
                -- Statistical values
                count INTEGER NOT NULL,
                mean_value REAL NOT NULL,
                median_value REAL NOT NULL,
                std_dev REAL,
                min_value REAL NOT NULL,
                max_value REAL NOT NULL,
                
                -- Confidence metrics
                confidence_interval_95_lower REAL,
                confidence_interval_95_upper REAL,
                
                last_updated TEXT NOT NULL,  -- ISO8601 timestamp
                
                UNIQUE(ec_number, parameter_type, organism, substrate)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX idx_brenda_stats
            ON brenda_statistics(ec_number, parameter_type, organism)
        """)
        
        # Table 7: Learned Patterns (Phase 3)
        cursor.execute("""
            CREATE TABLE learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- Pattern Classification
                pattern_type TEXT NOT NULL CHECK(pattern_type IN ('ec_class', 'ec_specific', 'organism', 'pathway')),
                ec_class TEXT,           -- e.g., '2.7' for transferases
                ec_number TEXT,          -- Full EC number for specific patterns
                organism_group TEXT,     -- e.g., 'mammals', 'yeast', 'bacteria'
                organism TEXT,           -- Specific organism
                pathway_context TEXT,    -- Optional pathway classification
                
                -- Parameter Statistics
                param_type TEXT NOT NULL CHECK(param_type IN ('vmax', 'km', 'kcat', 'lambda', 'delay')),
                param_mean REAL NOT NULL,
                param_std_dev REAL NOT NULL,
                param_median REAL,
                param_min REAL,
                param_max REAL,
                
                -- Confidence Metrics
                sample_size INTEGER NOT NULL,
                confidence_score REAL NOT NULL CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
                variance_penalty REAL DEFAULT 0.0,  -- Penalty for high variance
                
                -- Source Tracking
                source_ids TEXT,         -- JSON array of parameter IDs used to learn pattern
                last_updated TEXT NOT NULL,
                
                UNIQUE(pattern_type, ec_class, ec_number, organism_group, organism, pathway_context, param_type)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX idx_learned_ec
            ON learned_patterns(ec_class, param_type)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_learned_organism
            ON learned_patterns(organism, param_type)
        """)
        
        # Table 8: Pattern Performance (Phase 3)
        cursor.execute("""
            CREATE TABLE pattern_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER NOT NULL,
                
                -- Usage Statistics
                applications INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,  -- user_rating >= 0
                failure_count INTEGER DEFAULT 0,  -- user_rating < 0
                avg_user_rating REAL,
                
                -- Performance Metrics
                last_applied TEXT,
                last_rating_date TEXT,
                
                FOREIGN KEY (pattern_id) REFERENCES learned_patterns(id) ON DELETE CASCADE,
                UNIQUE(pattern_id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX idx_pattern_perf
            ON pattern_performance(pattern_id, avg_user_rating DESC)
        """)
        
        # Table 9: Schema Version
        cursor.execute("""
            CREATE TABLE schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (self.SCHEMA_VERSION,))
        
        # Insert default organism compatibility data
        self._insert_default_compatibility(conn)
        
        conn.commit()
        self.logger.info("Database schema created successfully")
    
    def _insert_default_compatibility(self, conn: sqlite3.Connection):
        """Insert default organism compatibility data.
        
        Args:
            conn: Database connection
        """
        cursor = conn.cursor()
        
        # Default compatibility scores based on evolutionary distance
        defaults = [
            # Human cross-references
            ("Homo sapiens", "Homo sapiens", None, 1.0, "Exact match"),
            ("Rattus norvegicus", "Homo sapiens", None, 0.85, "Mammalian (close)"),
            ("Mus musculus", "Homo sapiens", None, 0.85, "Mammalian (close)"),
            ("Sus scrofa", "Homo sapiens", None, 0.80, "Mammalian (moderate)"),
            ("Saccharomyces cerevisiae", "Homo sapiens", "EC 2.7.1", 0.75, "Glycolysis conserved"),
            ("Saccharomyces cerevisiae", "Homo sapiens", "EC 1.1.1", 0.70, "TCA cycle conserved"),
            ("Saccharomyces cerevisiae", "Homo sapiens", None, 0.60, "Eukaryotic (general)"),
            ("Escherichia coli", "Homo sapiens", "EC 2.7.1", 0.50, "Glycolysis partially conserved"),
            ("Escherichia coli", "Homo sapiens", None, 0.40, "Prokaryotic (distant)"),
            
            # Yeast cross-references
            ("Saccharomyces cerevisiae", "Saccharomyces cerevisiae", None, 1.0, "Exact match"),
            ("Homo sapiens", "Saccharomyces cerevisiae", None, 0.60, "Reverse: human→yeast"),
            
            # E. coli cross-references
            ("Escherichia coli", "Escherichia coli", None, 1.0, "Exact match"),
            
            # Generic/in vitro data
            ("generic", "Homo sapiens", None, 0.50, "In vitro data (no organism)"),
            ("generic", "Saccharomyces cerevisiae", None, 0.50, "In vitro data (no organism)"),
            ("generic", "Escherichia coli", None, 0.50, "In vitro data (no organism)"),
        ]
        
        cursor.executemany("""
            INSERT INTO organism_compatibility 
            (source_organism, target_organism, enzyme_class, compatibility_score, notes)
            VALUES (?, ?, ?, ?, ?)
        """, defaults)
        
        self.logger.info(f"Inserted {len(defaults)} default organism compatibility entries")
    
    def _migrate_schema(self, conn: sqlite3.Connection, from_version: int):
        """Migrate database schema to current version.
        
        Args:
            conn: Database connection
            from_version: Current schema version
        """
        cursor = conn.cursor()
        
        # Migration v1 -> v2: Phase 2 user feedback support
        if from_version < 2:
            self.logger.info("Migrating to schema v2: Adding undo columns")
            
            # Add undone column
            try:
                cursor.execute("""
                    ALTER TABLE transition_parameters 
                    ADD COLUMN undone INTEGER DEFAULT 0
                """)
            except sqlite3.OperationalError:
                pass  # Column might already exist
            
            # Add undo_timestamp column
            try:
                cursor.execute("""
                    ALTER TABLE transition_parameters 
                    ADD COLUMN undo_timestamp TEXT
                """)
            except sqlite3.OperationalError:
                pass  # Column might already exist
            
            # Note: Cannot modify CHECK constraint on existing table
            # user_rating constraint will only apply to new databases
            # Existing databases will need to manually handle -1/0/1 validation
            
            # Update schema version
            cursor.execute("UPDATE schema_version SET version = 2")
            self.logger.info("Migration to v2 complete")
        
        # Migration v2 -> v3: Phase 3 intelligent learning support
        if from_version < 3:
            self.logger.info("Migrating to schema v3: Adding learned patterns tables")
            
            # Add learned_patterns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    
                    -- Pattern Classification
                    pattern_type TEXT NOT NULL CHECK(pattern_type IN ('ec_class', 'ec_specific', 'organism', 'pathway')),
                    ec_class TEXT,
                    ec_number TEXT,
                    organism_group TEXT,
                    organism TEXT,
                    pathway_context TEXT,
                    
                    -- Parameter Statistics
                    param_type TEXT NOT NULL CHECK(param_type IN ('vmax', 'km', 'kcat', 'lambda', 'delay')),
                    param_mean REAL NOT NULL,
                    param_std_dev REAL NOT NULL,
                    param_median REAL,
                    param_min REAL,
                    param_max REAL,
                    
                    -- Confidence Metrics
                    sample_size INTEGER NOT NULL,
                    confidence_score REAL NOT NULL CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
                    variance_penalty REAL DEFAULT 0.0,
                    
                    -- Source Tracking
                    source_ids TEXT,
                    last_updated TEXT NOT NULL,
                    
                    UNIQUE(pattern_type, ec_class, ec_number, organism_group, organism, pathway_context, param_type)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_learned_ec
                ON learned_patterns(ec_class, param_type)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_learned_organism
                ON learned_patterns(organism, param_type)
            """)
            
            # Add pattern_performance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pattern_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id INTEGER NOT NULL,
                    
                    applications INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    avg_user_rating REAL,
                    
                    last_applied TEXT,
                    last_rating_date TEXT,
                    
                    FOREIGN KEY (pattern_id) REFERENCES learned_patterns(id) ON DELETE CASCADE,
                    UNIQUE(pattern_id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pattern_perf
                ON pattern_performance(pattern_id, avg_user_rating DESC)
            """)
            
            # Update schema version
            cursor.execute("UPDATE schema_version SET version = 3")
            self.logger.info("Migration to v3 complete")
    
    # ==================== Parameter Storage ====================
    
    def store_parameter(self, 
                       transition_type: str,
                       organism: str,
                       parameters: Dict[str, Any],
                       source: str,
                       confidence_score: float,
                       biological_semantics: Optional[str] = None,
                       ec_number: Optional[str] = None,
                       enzyme_name: Optional[str] = None,
                       reaction_id: Optional[str] = None,
                       temperature: Optional[float] = None,
                       ph: Optional[float] = None,
                       source_id: Optional[str] = None,
                       pubmed_id: Optional[str] = None,
                       notes: Optional[str] = None) -> int:
        """Store inferred parameter in database.
        
        Args:
            transition_type: 'immediate', 'timed', 'stochastic', or 'continuous'
            organism: Organism name (e.g., 'Homo sapiens')
            parameters: Type-specific parameters as dict
            source: Data source ('SABIO-RK', 'BioModels', 'Heuristic', etc.)
            confidence_score: 0.0-1.0
            biological_semantics: Optional semantic label
            ec_number: Optional EC number
            enzyme_name: Optional enzyme name
            reaction_id: Optional KEGG reaction ID
            temperature: Optional temperature (°C)
            ph: Optional pH
            source_id: Optional source-specific ID
            pubmed_id: Optional PubMed ID
            notes: Optional notes
        
        Returns:
            int: ID of inserted parameter
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO transition_parameters (
                    transition_type, biological_semantics,
                    ec_number, enzyme_name, reaction_id, organism,
                    parameters, temperature, ph,
                    source, source_id, pubmed_id, confidence_score,
                    import_date, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transition_type, biological_semantics,
                ec_number, enzyme_name, reaction_id, organism,
                json.dumps(parameters), temperature, ph,
                source, source_id, pubmed_id, confidence_score,
                now, notes
            ))
            
            param_id = cursor.lastrowid
            self.logger.debug(f"Stored parameter ID {param_id} ({transition_type}, {organism})")
            return param_id
    
    def get_parameter(self, parameter_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve parameter by ID.
        
        Args:
            parameter_id: Parameter ID
        
        Returns:
            Dict with parameter data, or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM transition_parameters WHERE id = ?
            """, (parameter_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None
    
    def query_parameters(self,
                        transition_type: Optional[str] = None,
                        ec_number: Optional[str] = None,
                        reaction_id: Optional[str] = None,
                        organism: Optional[str] = None,
                        min_confidence: float = 0.0,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Query parameters with filters.
        
        Args:
            transition_type: Filter by transition type
            ec_number: Filter by EC number
            reaction_id: Filter by reaction ID
            organism: Filter by organism
            min_confidence: Minimum confidence score
            limit: Maximum results
        
        Returns:
            List of parameter dicts
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query dynamically
            query = "SELECT * FROM transition_parameters WHERE confidence_score >= ?"
            params = [min_confidence]
            
            if transition_type:
                query += " AND transition_type = ?"
                params.append(transition_type)
            
            if ec_number:
                query += " AND ec_number = ?"
                params.append(ec_number)
            
            if reaction_id:
                query += " AND reaction_id = ?"
                params.append(reaction_id)
            
            if organism:
                query += " AND organism = ?"
                params.append(organism)
            
            query += " ORDER BY confidence_score DESC, usage_count DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                results.append(self._row_to_dict(row))
            
            self.logger.debug(f"Query returned {len(results)} parameters")
            return results
    
    def update_usage(self, parameter_id: int):
        """Update usage statistics for a parameter.
        
        Args:
            parameter_id: Parameter ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute("""
                UPDATE transition_parameters
                SET usage_count = usage_count + 1,
                    last_used = ?
                WHERE id = ?
            """, (now, parameter_id))
            
            self.logger.debug(f"Updated usage for parameter {parameter_id}")
    
    def set_user_rating(self, parameter_id: int, rating: int):
        """Set user rating for a parameter.
        
        Args:
            parameter_id: Parameter ID
            rating: 1-5 stars
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be 1-5")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE transition_parameters
                SET user_rating = ?
                WHERE id = ?
            """, (rating, parameter_id))
            
            self.logger.debug(f"Set rating {rating} for parameter {parameter_id}")
    
    # ==================== Cache Management ====================
    
    def cache_query(self,
                   query_key: str,
                   recommended_id: int,
                   alternatives: List[int],
                   confidence_score: float):
        """Cache query result for fast lookup.
        
        Args:
            query_key: Hash key for query (e.g., "continuous|EC:2.7.1.1|Homo sapiens")
            recommended_id: ID of recommended parameter
            alternatives: List of alternative parameter IDs
            confidence_score: Confidence score of recommendation
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO heuristic_cache
                (query_key, recommended_parameter_id, alternatives, confidence_score, last_updated, hit_count)
                VALUES (?, ?, ?, ?, ?, COALESCE((SELECT hit_count FROM heuristic_cache WHERE query_key = ?), 0))
            """, (query_key, recommended_id, json.dumps(alternatives), confidence_score, now, query_key))
            
            self.logger.debug(f"Cached query: {query_key}")
    
    def get_cached_query(self, query_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached query result.
        
        Args:
            query_key: Hash key for query
        
        Returns:
            Dict with cached result, or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM heuristic_cache WHERE query_key = ?
            """, (query_key,))
            
            row = cursor.fetchone()
            if row:
                # Increment hit count
                cursor.execute("""
                    UPDATE heuristic_cache
                    SET hit_count = hit_count + 1
                    WHERE query_key = ?
                """, (query_key,))
                
                result = dict(row)
                result['alternatives'] = json.loads(result['alternatives'])
                self.logger.debug(f"Cache hit: {query_key}")
                return result
            
            self.logger.debug(f"Cache miss: {query_key}")
            return None
    
    def clear_cache(self, older_than_days: Optional[int] = None):
        """Clear query cache.
        
        Args:
            older_than_days: If specified, only clear entries older than N days
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if older_than_days:
                cutoff = datetime.now()
                # Simple approach: delete all for now
                # TODO: Implement proper date filtering
                cursor.execute("DELETE FROM heuristic_cache")
            else:
                cursor.execute("DELETE FROM heuristic_cache")
            
            deleted = cursor.rowcount
            self.logger.info(f"Cleared {deleted} cache entries")
    
    # ==================== Pathway Enrichments ====================
    
    def record_enrichment(self,
                         parameter_id: int,
                         transition_id: str,
                         pathway_id: Optional[str] = None,
                         pathway_name: Optional[str] = None,
                         reaction_id: Optional[str] = None,
                         project_path: Optional[str] = None):
        """Record that a parameter was applied to a transition.
        
        Args:
            parameter_id: Parameter ID
            transition_id: Transition ID in model
            pathway_id: Optional pathway ID (e.g., 'hsa00010')
            pathway_name: Optional pathway name
            reaction_id: Optional reaction ID
            project_path: Optional project file path
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO pathway_enrichments
                (pathway_id, pathway_name, reaction_id, transition_id, parameter_id, applied_date, project_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (pathway_id, pathway_name, reaction_id, transition_id, parameter_id, now, project_path))
            
            # Also update usage count (in same transaction)
            cursor.execute("""
                UPDATE transition_parameters
                SET usage_count = usage_count + 1,
                    last_used = ?
                WHERE id = ?
            """, (now, parameter_id))
            
            self.logger.debug(f"Recorded enrichment: parameter {parameter_id} → transition {transition_id}")
    
    def get_enrichment_history(self, 
                               pathway_id: Optional[str] = None,
                               transition_id: Optional[str] = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Get enrichment history.
        
        Args:
            pathway_id: Filter by pathway ID
            transition_id: Filter by transition ID
            limit: Maximum results
        
        Returns:
            List of enrichment records with parameter details
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT e.*, p.*
                FROM pathway_enrichments e
                JOIN transition_parameters p ON e.parameter_id = p.id
                WHERE 1=1
            """
            params = []
            
            if pathway_id:
                query += " AND e.pathway_id = ?"
                params.append(pathway_id)
            
            if transition_id:
                query += " AND e.transition_id = ?"
                params.append(transition_id)
            
            query += " ORDER BY e.applied_date DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            
            return results
    
    # ==================== Organism Compatibility ====================
    
    def get_compatibility_score(self,
                               source_organism: str,
                               target_organism: str,
                               enzyme_class: Optional[str] = None) -> float:
        """Get compatibility score between organisms.
        
        Args:
            source_organism: Source organism
            target_organism: Target organism
            enzyme_class: Optional enzyme class (e.g., 'EC 2.7.1')
        
        Returns:
            Compatibility score (0.0-1.0)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Try exact match with enzyme class
            if enzyme_class:
                cursor.execute("""
                    SELECT compatibility_score FROM organism_compatibility
                    WHERE source_organism = ? AND target_organism = ? AND enzyme_class = ?
                """, (source_organism, target_organism, enzyme_class))
                
                row = cursor.fetchone()
                if row:
                    return row[0]
            
            # Try match without enzyme class
            cursor.execute("""
                SELECT compatibility_score FROM organism_compatibility
                WHERE source_organism = ? AND target_organism = ? AND enzyme_class IS NULL
            """, (source_organism, target_organism))
            
            row = cursor.fetchone()
            if row:
                return row[0]
            
            # Default: very low confidence for unknown combinations
            self.logger.warning(f"No compatibility data for {source_organism} → {target_organism}")
            return 0.3
    
    # ==================== Statistics ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dict with statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total parameters
            cursor.execute("SELECT COUNT(*) FROM transition_parameters")
            stats['total_parameters'] = cursor.fetchone()[0]
            
            # Parameters by type
            cursor.execute("""
                SELECT transition_type, COUNT(*) 
                FROM transition_parameters 
                GROUP BY transition_type
            """)
            stats['by_type'] = dict(cursor.fetchall())
            
            # Parameters by source
            cursor.execute("""
                SELECT source, COUNT(*) 
                FROM transition_parameters 
                GROUP BY source
            """)
            stats['by_source'] = dict(cursor.fetchall())
            
            # Cache statistics
            cursor.execute("SELECT COUNT(*) FROM heuristic_cache")
            stats['cache_entries'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(hit_count) FROM heuristic_cache")
            stats['cache_hits'] = cursor.fetchone()[0] or 0
            
            # Enrichment history
            cursor.execute("SELECT COUNT(*) FROM pathway_enrichments")
            stats['total_enrichments'] = cursor.fetchone()[0]
            
            # Most used parameters
            cursor.execute("""
                SELECT id, enzyme_name, ec_number, usage_count
                FROM transition_parameters
                ORDER BY usage_count DESC
                LIMIT 10
            """)
            stats['most_used'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
    
    # ==================== BRENDA Data Management ====================
    
    def insert_brenda_raw_data(self, results: List[Dict[str, Any]]) -> int:
        """Bulk insert BRENDA query results into raw data table.
        
        Args:
            results: List of BRENDA result dictionaries with keys:
                    ec_number, parameter_type, value, unit, substrate,
                    organism, literature, commentary, quality
        
        Returns:
            Number of records inserted (duplicates skipped)
        """
        if not results:
            return 0
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            inserted = 0
            
            for result in results:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO brenda_raw_data
                        (ec_number, parameter_type, value, unit, substrate, organism,
                         literature, commentary, query_date, source_quality)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
                    """, (
                        result.get('ec_number', ''),
                        result.get('parameter_type', ''),
                        result.get('value', 0.0),
                        result.get('unit', ''),
                        result.get('substrate', ''),
                        result.get('organism', ''),
                        result.get('literature', ''),
                        result.get('commentary', ''),
                        result.get('quality', 0.0)
                    ))
                    if cursor.rowcount > 0:
                        inserted += 1
                except sqlite3.IntegrityError:
                    # Duplicate entry, skip
                    continue
            
            conn.commit()
            self.logger.info(f"Inserted {inserted}/{len(results)} BRENDA records")
            return inserted
    
    def query_brenda_data(self, 
                         ec_number: str = None,
                         parameter_type: str = None,
                         organism: str = None,
                         substrate: str = None,
                         min_quality: float = 0.0,
                         limit: int = None) -> List[Dict[str, Any]]:
        """Query BRENDA raw data with optional filters.
        
        Args:
            ec_number: EC number filter
            parameter_type: Parameter type (Km, kcat, Ki)
            organism: Organism name (partial match)
            substrate: Substrate name (partial match)
            min_quality: Minimum quality score (0.0-1.0)
            limit: Maximum records to return
        
        Returns:
            List of matching BRENDA records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM brenda_raw_data WHERE 1=1"
            params = []
            
            if ec_number:
                query += " AND ec_number = ?"
                params.append(ec_number)
            
            if parameter_type:
                query += " AND parameter_type = ?"
                params.append(parameter_type)
            
            if organism:
                query += " AND organism LIKE ?"
                params.append(f"%{organism}%")
            
            if substrate:
                query += " AND substrate LIKE ?"
                params.append(f"%{substrate}%")
            
            if min_quality > 0.0:
                query += " AND source_quality >= ?"
                params.append(min_quality)
            
            query += " ORDER BY source_quality DESC, query_date DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def calculate_brenda_statistics(self, 
                                    ec_number: str,
                                    parameter_type: str,
                                    organism: str = None,
                                    substrate: str = None) -> Dict[str, Any]:
        """Calculate statistics from BRENDA raw data and cache in statistics table.
        
        Args:
            ec_number: EC number
            parameter_type: Parameter type (Km, kcat, Ki)
            organism: Optional organism filter
            substrate: Optional substrate filter
        
        Returns:
            Statistics dictionary with mean, median, std_dev, etc.
        """
        # Query raw data
        raw_data = self.query_brenda_data(
            ec_number=ec_number,
            parameter_type=parameter_type,
            organism=organism,
            substrate=substrate
        )
        
        if not raw_data:
            return None
        
        # Extract values
        values = [float(row['value']) for row in raw_data if row['value'] is not None]
        
        if not values:
            return None
        
        # Calculate statistics
        import statistics
        stats = {
            'ec_number': ec_number,
            'parameter_type': parameter_type,
            'organism': organism or 'all',
            'substrate': substrate or 'all',
            'count': len(values),
            'mean_value': statistics.mean(values),
            'median_value': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0,
            'min_value': min(values),
            'max_value': max(values)
        }
        
        # Calculate 95% confidence interval (assuming normal distribution)
        if len(values) > 1:
            import math
            sem = stats['std_dev'] / math.sqrt(len(values))  # Standard error
            ci_margin = 1.96 * sem  # 95% CI
            stats['confidence_interval_95_lower'] = stats['mean_value'] - ci_margin
            stats['confidence_interval_95_upper'] = stats['mean_value'] + ci_margin
        else:
            stats['confidence_interval_95_lower'] = stats['mean_value']
            stats['confidence_interval_95_upper'] = stats['mean_value']
        
        # Cache in database
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO brenda_statistics
                (ec_number, parameter_type, organism, substrate, count,
                 mean_value, median_value, std_dev, min_value, max_value,
                 confidence_interval_95_lower, confidence_interval_95_upper, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                stats['ec_number'],
                stats['parameter_type'],
                stats['organism'],
                stats['substrate'],
                stats['count'],
                stats['mean_value'],
                stats['median_value'],
                stats['std_dev'],
                stats['min_value'],
                stats['max_value'],
                stats['confidence_interval_95_lower'],
                stats['confidence_interval_95_upper']
            ))
            conn.commit()
        
        self.logger.info(f"Calculated statistics for {ec_number} {parameter_type}: "
                        f"mean={stats['mean_value']:.3f}, n={stats['count']}")
        return stats
    
    def get_brenda_statistics(self,
                             ec_number: str,
                             parameter_type: str,
                             organism: str = None,
                             substrate: str = None) -> Dict[str, Any]:
        """Retrieve cached BRENDA statistics.
        
        Args:
            ec_number: EC number
            parameter_type: Parameter type (Km, kcat, Ki)
            organism: Optional organism filter
            substrate: Optional substrate filter
        
        Returns:
            Statistics dictionary or None if not cached
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM brenda_statistics
                WHERE ec_number = ? AND parameter_type = ?
                  AND organism = ? AND substrate = ?
            """, (ec_number, parameter_type, organism or 'all', substrate or 'all'))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_brenda_summary(self) -> Dict[str, Any]:
        """Get summary statistics of BRENDA data in database.
        
        Returns:
            Summary with counts by EC, parameter type, organism
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            summary = {}
            
            # Total records
            cursor.execute("SELECT COUNT(*) FROM brenda_raw_data")
            summary['total_records'] = cursor.fetchone()[0]
            
            # By parameter type
            cursor.execute("""
                SELECT parameter_type, COUNT(*) as count
                FROM brenda_raw_data
                GROUP BY parameter_type
            """)
            summary['by_parameter_type'] = dict(cursor.fetchall())
            
            # Unique EC numbers
            cursor.execute("SELECT COUNT(DISTINCT ec_number) FROM brenda_raw_data")
            summary['unique_ec_numbers'] = cursor.fetchone()[0]
            
            # Unique organisms
            cursor.execute("SELECT COUNT(DISTINCT organism) FROM brenda_raw_data")
            summary['unique_organisms'] = cursor.fetchone()[0]
            
            # Average quality
            cursor.execute("SELECT AVG(source_quality) FROM brenda_raw_data")
            summary['average_quality'] = cursor.fetchone()[0] or 0.0
            
            # Statistics cache
            cursor.execute("SELECT COUNT(*) FROM brenda_statistics")
            summary['cached_statistics'] = cursor.fetchone()[0]
            
            return summary
    
    # ==================== Utilities ====================
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert database row to dictionary.
        
        Args:
            row: SQLite row
        
        Returns:
            Dict with row data
        """
        result = dict(row)
        # Parse JSON fields
        if 'parameters' in result and result['parameters']:
            result['parameters'] = json.loads(result['parameters'])
        return result
    
    # ==================== Learned Patterns (Phase 3) ====================
    
    def store_learned_pattern(self,
                             pattern_type: str,
                             param_type: str,
                             param_mean: float,
                             param_std_dev: float,
                             sample_size: int,
                             confidence_score: float,
                             source_ids: List[int],
                             ec_class: Optional[str] = None,
                             ec_number: Optional[str] = None,
                             organism_group: Optional[str] = None,
                             organism: Optional[str] = None,
                             pathway_context: Optional[str] = None,
                             param_median: Optional[float] = None,
                             param_min: Optional[float] = None,
                             param_max: Optional[float] = None,
                             variance_penalty: float = 0.0) -> int:
        """Store a learned parameter pattern.
        
        Args:
            pattern_type: 'ec_class', 'ec_specific', 'organism', or 'pathway'
            param_type: 'vmax', 'km', 'kcat', 'lambda', or 'delay'
            param_mean: Mean parameter value
            param_std_dev: Standard deviation
            sample_size: Number of samples used
            confidence_score: Overall confidence (0.0-1.0)
            source_ids: List of parameter IDs used to learn pattern
            ec_class: Optional EC class (e.g., '2.7')
            ec_number: Optional full EC number
            organism_group: Optional organism group
            organism: Optional specific organism
            pathway_context: Optional pathway context
            param_median: Optional median value
            param_min: Optional minimum value
            param_max: Optional maximum value
            variance_penalty: Penalty for high variance (default 0.0)
            
        Returns:
            Pattern ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Convert source_ids to JSON
            source_ids_json = json.dumps(source_ids)
            
            cursor.execute("""
                INSERT OR REPLACE INTO learned_patterns
                (pattern_type, ec_class, ec_number, organism_group, organism, pathway_context,
                 param_type, param_mean, param_std_dev, param_median, param_min, param_max,
                 sample_size, confidence_score, variance_penalty, source_ids, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                pattern_type, ec_class, ec_number, organism_group, organism, pathway_context,
                param_type, param_mean, param_std_dev, param_median, param_min, param_max,
                sample_size, confidence_score, variance_penalty, source_ids_json
            ))
            
            pattern_id = cursor.lastrowid
            
            # Initialize performance tracking
            cursor.execute("""
                INSERT OR IGNORE INTO pattern_performance (pattern_id, applications)
                VALUES (?, 0)
            """, (pattern_id,))
            
            conn.commit()
            self.logger.info(f"Stored learned pattern {pattern_id} ({pattern_type}, {param_type})")
            return pattern_id
    
    def query_learned_pattern(self,
                             param_type: str,
                             ec_number: Optional[str] = None,
                             organism: Optional[str] = None,
                             min_confidence: float = 0.5) -> Optional[Dict[str, Any]]:
        """Query for best matching learned pattern.
        
        Tries in order:
        1. Exact EC + organism match
        2. EC class + organism match
        3. Exact EC match (any organism)
        4. EC class match (any organism)
        5. Organism match (any EC)
        
        Args:
            param_type: Parameter type to query
            ec_number: Optional EC number
            organism: Optional organism
            min_confidence: Minimum confidence threshold
            
        Returns:
            Pattern dict or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Try exact match first
            if ec_number and organism:
                cursor.execute("""
                    SELECT * FROM learned_patterns
                    WHERE param_type = ?
                      AND ec_number = ?
                      AND organism = ?
                      AND confidence_score >= ?
                    ORDER BY confidence_score DESC, sample_size DESC
                    LIMIT 1
                """, (param_type, ec_number, organism, min_confidence))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
            
            # Try EC class + organism
            if ec_number and organism:
                ec_class = '.'.join(ec_number.split('.')[:2])
                cursor.execute("""
                    SELECT * FROM learned_patterns
                    WHERE param_type = ?
                      AND ec_class = ?
                      AND organism = ?
                      AND confidence_score >= ?
                    ORDER BY confidence_score DESC, sample_size DESC
                    LIMIT 1
                """, (param_type, ec_class, organism, min_confidence))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
            
            # Try EC-specific (any organism)
            if ec_number:
                cursor.execute("""
                    SELECT * FROM learned_patterns
                    WHERE param_type = ?
                      AND ec_number = ?
                      AND confidence_score >= ?
                    ORDER BY confidence_score DESC, sample_size DESC
                    LIMIT 1
                """, (param_type, ec_number, min_confidence))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
            
            # Try EC class (any organism)
            if ec_number:
                ec_class = '.'.join(ec_number.split('.')[:2])
                cursor.execute("""
                    SELECT * FROM learned_patterns
                    WHERE param_type = ?
                      AND ec_class = ?
                      AND confidence_score >= ?
                    ORDER BY confidence_score DESC, sample_size DESC
                    LIMIT 1
                """, (param_type, ec_class, min_confidence))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
            
            # Try organism match (any EC)
            if organism:
                cursor.execute("""
                    SELECT * FROM learned_patterns
                    WHERE param_type = ?
                      AND organism = ?
                      AND confidence_score >= ?
                    ORDER BY confidence_score DESC, sample_size DESC
                    LIMIT 1
                """, (param_type, organism, min_confidence))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
            
            return None
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get statistics about learned patterns.
        
        Returns:
            Statistics dict
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Count patterns by type
            cursor.execute("""
                SELECT pattern_type, COUNT(*) as count
                FROM learned_patterns
                GROUP BY pattern_type
            """)
            patterns_by_type = {row['pattern_type']: row['count'] for row in cursor.fetchall()}
            
            # Total sample size
            cursor.execute("SELECT SUM(sample_size) as total FROM learned_patterns")
            total_samples = cursor.fetchone()['total'] or 0
            
            # Average confidence
            cursor.execute("SELECT AVG(confidence_score) as avg_conf FROM learned_patterns")
            avg_confidence = cursor.fetchone()['avg_conf'] or 0.0
            
            # Best patterns
            cursor.execute("""
                SELECT param_type, ec_class, organism, confidence_score, sample_size
                FROM learned_patterns
                ORDER BY confidence_score DESC, sample_size DESC
                LIMIT 10
            """)
            best_patterns = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_patterns': sum(patterns_by_type.values()),
                'patterns_by_type': patterns_by_type,
                'total_samples_used': total_samples,
                'avg_confidence': avg_confidence,
                'best_patterns': best_patterns
            }
    
    def close(self):
        """Close database connection (if needed).
        
        Note: Using context managers, so this is optional.
        """
        self.logger.info("Database closed")
