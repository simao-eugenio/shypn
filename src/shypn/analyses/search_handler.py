#!/usr/bin/env python3
"""Search Handler - Search for Petri net objects by name/label.

This module provides search functionality to find places and transitions
in a Petri net model for adding to analysis plots.
"""


class SearchHandler:
    """Handles searching for Petri net objects in a model.
    
    Provides methods to search for places and transitions by matching
    against their name (P1, T1, etc.) and label (user-defined text).
    """
    
    @staticmethod
    def search_places(model, query):
        """Search for places matching the query string.
        
        Searches both the system name (P1, P2, ...) and user-defined label.
        Case-insensitive matching.
        
        Args:
            model: ModelCanvasManager instance containing places list
            query: Search string to match against place name and label
            
        Returns:
            list: List of Place objects that match the query
        """
        if not query or not hasattr(model, 'places'):
            return []
        
        query_lower = query.lower().strip()
        if not query_lower:
            return []
        
        matches = []
        for place in model.places:
            # Match against name (P1, P2, etc.)
            if query_lower in place.name.lower():
                matches.append(place)
                continue
            
            # Match against label (user-defined text)
            if place.label and query_lower in place.label.lower():
                matches.append(place)
                continue
        
        return matches
    
    @staticmethod
    def search_transitions(model, query):
        """Search for transitions matching the query string.
        
        Searches both the system name (T1, T2, ...) and user-defined label.
        Case-insensitive matching.
        
        Args:
            model: ModelCanvasManager instance containing transitions list
            query: Search string to match against transition name and label
            
        Returns:
            list: List of Transition objects that match the query
        """
        if not query or not hasattr(model, 'transitions'):
            return []
        
        query_lower = query.lower().strip()
        if not query_lower:
            return []
        
        matches = []
        for transition in model.transitions:
            # Match against name (T1, T2, etc.)
            if query_lower in transition.name.lower():
                matches.append(transition)
                continue
            
            # Match against label (user-defined text)
            if transition.label and query_lower in transition.label.lower():
                matches.append(transition)
                continue
        
        return matches
    
    @staticmethod
    def format_result_summary(results, object_type):
        """Format search results into a human-readable summary string.
        
        For transitions, includes source/sink indicators:
        - ⊙ = Source transition (generates tokens)
        - ⊗ = Sink transition (consumes tokens)
        
        Args:
            results: List of Place or Transition objects
            object_type: String "place" or "transition" for display
            
        Returns:
            str: Formatted summary like "Found 3 transitions: T1(⊙), T2, T3(⊗)"
        """
        if not results:
            return f"No {object_type}s found"
        
        count = len(results)
        plural = "s" if count != 1 else ""
        
        # Create list of names with type indicators for transitions
        names = []
        for obj in results[:10]:  # Limit to first 10 for display
            if object_type == "transition":
                # Add source/sink indicator
                is_source = getattr(obj, 'is_source', False)
                is_sink = getattr(obj, 'is_sink', False)
                
                if is_source:
                    names.append(f"{obj.name}(⊙)")  # Source symbol
                elif is_sink:
                    names.append(f"{obj.name}(⊗)")  # Sink symbol
                else:
                    names.append(obj.name)
            else:
                names.append(obj.name)
        
        names_str = ", ".join(names)
        
        if count > 10:
            names_str += f", ... (+{count - 10} more)"
        
        return f"Found {count} {object_type}{plural}: {names_str}"
