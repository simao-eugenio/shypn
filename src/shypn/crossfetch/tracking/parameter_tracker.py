#!/usr/bin/env python3
"""Parameter tracker for enrichment provenance.

Tracks when parameters are applied to transitions, enabling:
- Enrichment history and audit trails
- Undo/redo operations
- Usage analytics for learning
- Reproducibility and provenance
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime


class ParameterTracker:
    """Tracks parameter applications to transitions.
    
    Records all parameter applications with full metadata for provenance,
    analytics, and potential undo operations.
    
    Attributes:
        db: HeuristicDatabase instance
        logger: Logger instance
    """
    
    def __init__(self, database):
        """Initialize parameter tracker.
        
        Args:
            database: HeuristicDatabase instance
        """
        self.db = database
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def track_application(self,
                         transition_id: str,
                         parameters: Dict[str, Any],
                         source: str,
                         transition_type: str = 'continuous',
                         ec_number: Optional[str] = None,
                         reaction_id: Optional[str] = None,
                         organism: Optional[str] = None,
                         pathway_id: Optional[str] = None,
                         pathway_name: Optional[str] = None,
                         project_path: Optional[str] = None,
                         confidence_score: Optional[float] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> int:
        """Track parameter application to a transition.
        
        Args:
            transition_id: Transition identifier
            parameters: Applied parameters dict (e.g., {'vmax': 226.0, 'km': 0.1})
            source: Data source ('SABIO-RK', 'BRENDA', 'heuristic', etc.)
            transition_type: Type of transition ('continuous', 'immediate', etc.)
            ec_number: Optional EC number
            reaction_id: Optional reaction ID
            organism: Optional organism name
            pathway_id: Optional pathway identifier
            pathway_name: Optional pathway name
            project_path: Optional project file path
            confidence_score: Confidence score (auto-calculated if None)
            metadata: Optional additional metadata
        
        Returns:
            Parameter ID from database
        """
        try:
            # Calculate confidence if not provided
            if confidence_score is None:
                confidence_score = self._calculate_confidence(
                    source=source,
                    usage_count=0,
                    user_rating=None
                )
            
            # Store parameter in database
            param_id = self.db.store_parameter(
                transition_type=transition_type,
                organism=organism or 'unknown',
                parameters=parameters,
                source=source,
                confidence_score=confidence_score,
                ec_number=ec_number,
                reaction_id=reaction_id,
                temperature=metadata.get('temperature') if metadata else None,
                ph=metadata.get('ph') if metadata else None,
                source_id=metadata.get('source_id') if metadata else None,
                pubmed_id=metadata.get('pubmed_id') if metadata else None,
                notes=metadata.get('notes') if metadata else None
            )
            
            # Record enrichment
            self.db.record_enrichment(
                parameter_id=param_id,
                transition_id=transition_id,
                pathway_id=pathway_id,
                pathway_name=pathway_name,
                reaction_id=reaction_id,
                project_path=project_path
            )
            
            self.logger.info(
                f"Tracked application: {source} → {transition_id} "
                f"(param_id={param_id})"
            )
            
            return param_id
            
        except Exception as e:
            self.logger.error(f"Failed to track application: {e}")
            return -1
    
    def get_transition_history(self, 
                               transition_id: str,
                               limit: int = 10) -> List[Dict[str, Any]]:
        """Get enrichment history for a specific transition.
        
        Args:
            transition_id: Transition identifier
            limit: Maximum records to return
        
        Returns:
            List of enrichment records
        """
        return self.db.get_enrichment_history(
            transition_id=transition_id,
            limit=limit
        )
    
    def get_pathway_history(self,
                           pathway_id: str,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Get enrichment history for a pathway.
        
        Args:
            pathway_id: Pathway identifier
            limit: Maximum records to return
        
        Returns:
            List of enrichment records
        """
        return self.db.get_enrichment_history(
            pathway_id=pathway_id,
            limit=limit
        )
    
    def get_recent_applications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get most recent parameter applications.
        
        Args:
            limit: Maximum records to return
        
        Returns:
            List of recent enrichment records
        """
        return self.db.get_enrichment_history(limit=limit)
    
    def get_source_statistics(self, source: str) -> Dict[str, Any]:
        """Get statistics for a specific source.
        
        Args:
            source: Source name ('SABIO-RK', 'BRENDA', etc.)
        
        Returns:
            Dict with application counts, average confidence, etc.
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total applications from source
            cursor.execute("""
                SELECT COUNT(*) 
                FROM transition_parameters 
                WHERE source = ?
            """, (source,))
            total = cursor.fetchone()[0]
            
            # Average confidence
            cursor.execute("""
                SELECT AVG(confidence_score)
                FROM transition_parameters
                WHERE source = ?
            """, (source,))
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            # Most used
            cursor.execute("""
                SELECT COUNT(*)
                FROM transition_parameters
                WHERE source = ? AND usage_count > 0
            """, (source,))
            used = cursor.fetchone()[0]
            
            # Average rating
            cursor.execute("""
                SELECT AVG(user_rating)
                FROM transition_parameters
                WHERE source = ? AND user_rating IS NOT NULL
            """, (source,))
            avg_rating = cursor.fetchone()[0]
            
            return {
                'source': source,
                'total_applications': total,
                'used_count': used,
                'avg_confidence': round(avg_confidence, 3),
                'avg_user_rating': round(avg_rating, 2) if avg_rating else None
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get overall tracking summary.
        
        Returns:
            Dict with total applications, sources breakdown, etc.
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total tracked
            cursor.execute("SELECT COUNT(*) FROM pathway_enrichments")
            total_enrichments = cursor.fetchone()[0]
            
            # By source
            cursor.execute("""
                SELECT p.source, COUNT(*) as count
                FROM pathway_enrichments e
                JOIN transition_parameters p ON e.parameter_id = p.id
                GROUP BY p.source
            """)
            by_source = dict(cursor.fetchall())
            
            # Unique transitions
            cursor.execute("SELECT COUNT(DISTINCT transition_id) FROM pathway_enrichments")
            unique_transitions = cursor.fetchone()[0]
            
            # Unique pathways
            cursor.execute("""
                SELECT COUNT(DISTINCT pathway_id) 
                FROM pathway_enrichments 
                WHERE pathway_id IS NOT NULL
            """)
            unique_pathways = cursor.fetchone()[0]
            
            return {
                'total_enrichments': total_enrichments,
                'unique_transitions_enriched': unique_transitions,
                'unique_pathways_enriched': unique_pathways,
                'by_source': by_source
            }
    
    # ========================================================================
    # Phase 2: User Feedback & History Management
    # ========================================================================
    
    def update_rating(self, 
                     parameter_id: int, 
                     rating: int, 
                     comment: str = "") -> bool:
        """Update user rating for a parameter application.
        
        Updates the rating, comment, and recalculates confidence score.
        Increments usage_count to track engagement.
        
        Args:
            parameter_id: ID of parameter record
            rating: User rating (-1: poor, 0: neutral, 1: good)
            comment: Optional user comment
        
        Returns:
            bool: True if update successful
        """
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current record
                cursor.execute("""
                    SELECT source, usage_count, user_rating
                    FROM transition_parameters
                    WHERE id = ?
                """, (parameter_id,))
                
                row = cursor.fetchone()
                if not row:
                    self.logger.error(f"Parameter {parameter_id} not found")
                    return False
                
                source, usage_count, old_rating = row
                
                # Update rating and comment
                cursor.execute("""
                    UPDATE transition_parameters
                    SET user_rating = ?,
                        notes = ?,
                        usage_count = usage_count + 1
                    WHERE id = ?
                """, (rating, comment, parameter_id))
                
                # Recalculate confidence
                new_confidence = self._calculate_confidence(
                    source=source,
                    usage_count=usage_count + 1,
                    user_rating=rating
                )
                
                cursor.execute("""
                    UPDATE transition_parameters
                    SET confidence_score = ?
                    WHERE id = ?
                """, (new_confidence, parameter_id))
                
                conn.commit()
                
                self.logger.info(
                    f"Updated rating for parameter {parameter_id}: "
                    f"{old_rating} → {rating}, confidence: {new_confidence:.2f}"
                )
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update rating: {e}")
            return False
    
    def get_filtered_history(self,
                            source: Optional[str] = None,
                            pathway_id: Optional[str] = None,
                            transition_id: Optional[str] = None,
                            date_range: Optional[tuple] = None,
                            rating: Optional[int] = None,
                            include_undone: bool = False,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get enrichment history with filters.
        
        Args:
            source: Filter by source ('SABIO-RK', 'BRENDA', etc.)
            pathway_id: Filter by pathway ID
            transition_id: Filter by transition ID
            date_range: Tuple of (start_date, end_date) strings
            rating: Filter by user rating (-1, 0, 1)
            include_undone: Include undone applications
            limit: Maximum records to return
        
        Returns:
            List of enrichment records matching filters
        """
        try:
            query = """
                SELECT 
                    p.id as parameter_id,
                    p.source,
                    p.organism,
                    p.parameters,
                    p.confidence_score,
                    p.user_rating,
                    p.notes,
                    p.usage_count,
                    p.ec_number,
                    p.import_date,
                    p.undone,
                    p.undo_timestamp,
                    e.transition_id,
                    e.pathway_id,
                    e.pathway_name,
                    e.applied_date
                FROM transition_parameters p
                LEFT JOIN pathway_enrichments e ON p.id = e.parameter_id
                WHERE 1=1
            """
            params = []
            
            if source:
                query += " AND p.source = ?"
                params.append(source)
            
            if pathway_id:
                query += " AND e.pathway_id = ?"
                params.append(pathway_id)
            
            if transition_id:
                query += " AND e.transition_id = ?"
                params.append(transition_id)
            
            if not include_undone:
                query += " AND (p.undone IS NULL OR p.undone = 0)"
            
            if rating is not None:
                query += " AND p.user_rating = ?"
                params.append(rating)
            
            if date_range:
                start, end = date_range
                query += " AND e.applied_date BETWEEN ? AND ?"
                params.extend([start, end])
            
            query += " ORDER BY e.applied_date DESC LIMIT ?"
            params.append(limit)
            
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    # Parse JSON parameters if stored as string
                    if isinstance(record.get('parameters'), str):
                        import json
                        try:
                            record['parameters'] = json.loads(record['parameters'])
                        except:
                            pass
                    results.append(record)
                
                self.logger.debug(
                    f"Retrieved {len(results)} filtered history records"
                )
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to get filtered history: {e}")
            return []
    
    def undo_application(self, parameter_id: int) -> Dict[str, Any]:
        """Undo a parameter application.
        
        Marks the application as undone (doesn't delete for audit trail).
        Returns previous parameter values for reverting transition state.
        
        Args:
            parameter_id: ID of parameter application to undo
        
        Returns:
            Dict with:
                - success: bool
                - transition_id: str
                - previous_parameters: Dict or None
                - message: str
        """
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get the record
                cursor.execute("""
                    SELECT p.id, p.undone, e.transition_id, e.applied_date
                    FROM transition_parameters p
                    LEFT JOIN pathway_enrichments e ON p.id = e.parameter_id
                    WHERE p.id = ?
                """, (parameter_id,))
                
                row = cursor.fetchone()
                if not row:
                    return {
                        'success': False,
                        'message': f'Parameter {parameter_id} not found'
                    }
                
                param_id, undone, transition_id, applied_date = row
                
                if undone:
                    return {
                        'success': False,
                        'message': 'Application already undone'
                    }
                
                # Get previous parameters (look for earlier application)
                previous = self._get_previous_parameters(
                    transition_id=transition_id,
                    before_date=applied_date
                )
                
                # Mark as undone
                cursor.execute("""
                    UPDATE transition_parameters
                    SET undone = 1,
                        undo_timestamp = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (parameter_id,))
                
                conn.commit()
                
                self.logger.info(f"Undone parameter application {parameter_id}")
                
                return {
                    'success': True,
                    'transition_id': transition_id,
                    'previous_parameters': previous,
                    'message': 'Application undone successfully'
                }
                
        except Exception as e:
            self.logger.error(f"Failed to undo application: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def _get_previous_parameters(self,
                                 transition_id: str,
                                 before_date: str) -> Optional[Dict[str, Any]]:
        """Get previous parameters applied to a transition.
        
        Args:
            transition_id: Transition identifier
            before_date: Get parameters applied before this date
        
        Returns:
            Previous parameters dict or None if no previous application
        """
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT p.parameters
                    FROM transition_parameters p
                    LEFT JOIN pathway_enrichments e ON p.id = e.parameter_id
                    WHERE e.transition_id = ?
                      AND e.applied_date < ?
                      AND (p.undone IS NULL OR p.undone = 0)
                    ORDER BY e.applied_date DESC
                    LIMIT 1
                """, (transition_id, before_date))
                
                row = cursor.fetchone()
                if row and row[0]:
                    # Parse JSON if stored as string
                    params = row[0]
                    if isinstance(params, str):
                        import json
                        return json.loads(params)
                    return params
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get previous parameters: {e}")
            return None
    
    def _calculate_confidence(self,
                             source: str,
                             usage_count: int,
                             user_rating: Optional[int]) -> float:
        """Calculate parameter confidence score.
        
        Factors:
        - Source baseline (SABIO-RK: 0.85, BRENDA: 0.80, Heuristic: 0.70)
        - Usage boost (+1% per use, max +10%)
        - User rating influence (-15% poor, 0% neutral, +10% good)
        
        Args:
            source: Data source name
            usage_count: Number of times parameters used
            user_rating: User rating (-1, 0, 1, or None)
                        Note: Legacy 1-5 ratings are converted
        
        Returns:
            float: Confidence score 0.0-1.0
        """
        # Base confidence by source
        base_confidence = {
            'SABIO-RK': 0.85,
            'BRENDA': 0.80,
            'Heuristic': 0.70,
            'heuristic': 0.70
        }.get(source, 0.60)
        
        # Usage boost (max +10%)
        usage_boost = min(0.10, usage_count * 0.01)
        
        # Rating influence
        # Support both -1/0/1 (new) and 1-5 (legacy) ratings
        if user_rating is not None:
            # New scale: -1/0/1
            if user_rating in [-1, 0, 1]:
                rating_factor = {
                    -1: -0.15,  # Poor rating
                    0: 0.0,     # Neutral/unsure
                    1: +0.10,   # Good rating
                }[user_rating]
            # Legacy 1-5 scale
            elif user_rating >= 4:  # 4-5: Good
                rating_factor = +0.10
            elif user_rating <= 2:  # 1-2: Poor
                rating_factor = -0.15
            elif user_rating == 3:  # 3: Neutral
                rating_factor = 0.0
            else:
                rating_factor = 0.0
        else:
            rating_factor = 0.0
        
        # Calculate final confidence
        confidence = base_confidence + usage_boost + rating_factor
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))
