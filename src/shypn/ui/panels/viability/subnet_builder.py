"""Subnet builder - extract and analyze subnet from localities.

Builds a Subnet object from multiple localities, classifying places as
boundary vs internal, finding dependencies between localities, and analyzing
subnet topology.
"""
from typing import List, Set, Tuple, Dict, Any
from .investigation import Subnet, Dependency


class SubnetBuilder:
    """Extract and analyze subnet structure from localities."""
    
    def build_subnet(self, localities: List[Any]) -> Subnet:
        """Build subnet from multiple localities.
        
        IMPORTANT: Only builds subnet if localities are CONNECTED through shared places.
        If localities don't share any places, they form disconnected components and
        cannot be analyzed as a subnet.
        
        Args:
            localities: List of Locality objects
            
        Returns:
            Subnet object with classified places and dependencies
            
        Raises:
            ValueError: If localities are not connected (no shared places)
        """
        if not localities:
            return Subnet()
        
        if len(localities) == 1:
            # Single locality - simple case
            return self._build_single_locality_subnet(localities[0])
        
        # Multiple localities - check if they're connected
        if not self._are_localities_connected(localities):
            raise ValueError(
                "Cannot form subnet: selected localities are not connected. "
                "Localities must share at least one place to form a valid subnet."
            )
        
        # Multiple localities - full subnet
        subnet = Subnet()
        
        # Collect all transitions
        for locality in localities:
            subnet.transitions.add(locality.transition.id)
        
        # Collect all places and arcs
        for locality in localities:
            # Input places
            for place in locality.input_places:
                subnet.places.add(place.id)
            # Output places
            for place in locality.output_places:
                subnet.places.add(place.id)
            # Input arcs
            for arc in locality.input_arcs:
                subnet.arcs.add(arc.id)
            # Output arcs
            for arc in locality.output_arcs:
                subnet.arcs.add(arc.id)
        
        # Classify places as boundary vs internal
        boundary, internal = self.classify_places(subnet.places, subnet.transitions, localities)
        subnet.boundary_places = boundary
        subnet.internal_places = internal
        
        # Identify boundary inputs and outputs
        subnet.boundary_inputs, subnet.boundary_outputs = self._identify_boundary_io(
            subnet, localities
        )
        
        # Find dependencies between localities
        subnet.dependencies = self.find_dependencies(subnet, localities)
        
        return subnet
    
    def _are_localities_connected(self, localities: List[Any]) -> bool:
        """Check if localities are connected through shared places.
        
        Localities are connected if they form a connected graph where:
        - Nodes are localities (transitions)
        - Edges exist when two localities share at least one place
        
        Args:
            localities: List of Locality objects
            
        Returns:
            True if all localities form a connected component, False otherwise
        """
        if len(localities) <= 1:
            return True
        
        # Build adjacency map: locality index → set of connected locality indices
        adjacency = {i: set() for i in range(len(localities))}
        
        # Find shared places between each pair of localities
        for i in range(len(localities)):
            places_i = self._get_all_places(localities[i])
            
            for j in range(i + 1, len(localities)):
                places_j = self._get_all_places(localities[j])
                
                # Check if they share any place
                if places_i & places_j:  # Set intersection
                    adjacency[i].add(j)
                    adjacency[j].add(i)
        
        # Check if graph is connected using BFS
        visited = set()
        queue = [0]  # Start from first locality
        visited.add(0)
        
        while queue:
            current = queue.pop(0)
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # All localities should be visited if connected
        return len(visited) == len(localities)
    
    def _get_all_places(self, locality: Any) -> Set[str]:
        """Get all place IDs (inputs and outputs) for a locality.
        
        Args:
            locality: Locality object
            
        Returns:
            Set of place IDs
        """
        places = set()
        for place in locality.input_places:
            places.add(place.id)
        for place in locality.output_places:
            places.add(place.id)
        return places
    
    def _build_single_locality_subnet(self, locality: Any) -> Subnet:
        """Build subnet from single locality (all places are boundary).
        
        Args:
            locality: Locality object
            
        Returns:
            Subnet with single transition
        """
        subnet = Subnet()
        subnet.transitions.add(locality.transition.id)
        
        # All places
        for place in locality.input_places:
            subnet.places.add(place.id)
            subnet.boundary_places.add(place.id)
            subnet.boundary_inputs.append(place.id)
        
        for place in locality.output_places:
            subnet.places.add(place.id)
            subnet.boundary_places.add(place.id)
            subnet.boundary_outputs.append(place.id)
        
        # All arcs
        for arc in locality.input_arcs:
            subnet.arcs.add(arc.id)
        for arc in locality.output_arcs:
            subnet.arcs.add(arc.id)
        
        return subnet
    
    def classify_places(
        self, 
        places: Set[str], 
        transitions: Set[str], 
        localities: List[Any]
    ) -> Tuple[Set[str], Set[str]]:
        """Classify places as boundary (external connections) vs internal.
        
        A place is on the boundary if it has arcs to/from transitions
        outside the subnet.
        
        Args:
            places: Set of place IDs in subnet
            transitions: Set of transition IDs in subnet
            localities: List of Locality objects
            
        Returns:
            Tuple of (boundary_places, internal_places)
        """
        boundary = set()
        internal = set()
        
        # Build map of place → transitions that use it
        place_to_transitions = self._build_place_transition_map(localities)
        
        for place_id in places:
            # Get all transitions connected to this place
            connected_transitions = place_to_transitions.get(place_id, set())
            
            # Check if any connected transition is outside subnet
            has_external = False
            for trans_id in connected_transitions:
                if trans_id not in transitions:
                    has_external = True
                    break
            
            if has_external:
                boundary.add(place_id)
            else:
                internal.add(place_id)
        
        return boundary, internal
    
    def _build_place_transition_map(self, localities: List[Any]) -> Dict[str, Set[str]]:
        """Build map of place ID → set of transition IDs connected to it.
        
        Args:
            localities: List of Locality objects
            
        Returns:
            Dict mapping place IDs to sets of transition IDs
        """
        place_map = {}
        
        for locality in localities:
            trans_id = locality.transition.id
            
            # Input places
            for place in locality.input_places:
                if place.id not in place_map:
                    place_map[place.id] = set()
                place_map[place.id].add(trans_id)
            
            # Output places
            for place in locality.output_places:
                if place.id not in place_map:
                    place_map[place.id] = set()
                place_map[place.id].add(trans_id)
        
        return place_map
    
    def _identify_boundary_io(
        self, 
        subnet: Subnet, 
        localities: List[Any]
    ) -> Tuple[List[str], List[str]]:
        """Identify which boundary places are inputs vs outputs.
        
        Args:
            subnet: Subnet object
            localities: List of Locality objects
            
        Returns:
            Tuple of (input_places, output_places)
        """
        inputs = []
        outputs = []
        
        # Places that are only inputs to subnet transitions
        for place_id in subnet.boundary_places:
            is_input = False
            is_output = False
            
            for locality in localities:
                # Check if place is input to this transition
                for place in locality.input_places:
                    if place.id == place_id:
                        is_input = True
                        break
                
                # Check if place is output from this transition
                for place in locality.output_places:
                    if place.id == place_id:
                        is_output = True
                        break
            
            # Classify based on usage
            if is_input and not is_output:
                inputs.append(place_id)
            elif is_output and not is_input:
                outputs.append(place_id)
            # If both, it's an intermediate place (not strictly boundary I/O)
        
        return inputs, outputs
    
    def find_dependencies(self, subnet: Subnet, localities: List[Any]) -> List[Dependency]:
        """Find flow dependencies between localities in subnet.
        
        A dependency exists when one locality's output is another locality's input.
        
        Args:
            subnet: Subnet object
            localities: List of Locality objects
            
        Returns:
            List of Dependency objects
        """
        dependencies = []
        
        # Build maps for efficient lookup
        place_to_producers = {}  # place_id → list of transition_ids that produce it
        place_to_consumers = {}  # place_id → list of transition_ids that consume it
        
        for locality in localities:
            trans_id = locality.transition.id
            
            # Output places (produced by this transition)
            for place in locality.output_places:
                if place.id not in place_to_producers:
                    place_to_producers[place.id] = []
                place_to_producers[place.id].append(trans_id)
            
            # Input places (consumed by this transition)
            for place in locality.input_places:
                if place.id not in place_to_consumers:
                    place_to_consumers[place.id] = []
                place_to_consumers[place.id].append(trans_id)
        
        # Find dependencies: producer → place → consumer
        for place_id in subnet.places:
            producers = place_to_producers.get(place_id, [])
            consumers = place_to_consumers.get(place_id, [])
            
            # Create dependency for each producer-consumer pair
            for producer in producers:
                for consumer in consumers:
                    if producer != consumer:  # Don't create self-dependencies
                        dep = Dependency(
                            source_transition_id=producer,
                            target_transition_id=consumer,
                            connecting_place_id=place_id
                        )
                        dependencies.append(dep)
        
        return dependencies
    
    def find_connected_components(self, localities: List[Any]) -> List[List[int]]:
        """Find connected components among localities.
        
        Useful for suggesting which localities can form valid subnets together.
        
        Args:
            localities: List of Locality objects
            
        Returns:
            List of connected components, where each component is a list of locality indices
        """
        if not localities:
            return []
        
        if len(localities) == 1:
            return [[0]]
        
        # Build adjacency map
        adjacency = {i: set() for i in range(len(localities))}
        
        for i in range(len(localities)):
            places_i = self._get_all_places(localities[i])
            
            for j in range(i + 1, len(localities)):
                places_j = self._get_all_places(localities[j])
                
                if places_i & places_j:
                    adjacency[i].add(j)
                    adjacency[j].add(i)
        
        # Find connected components using BFS
        components = []
        visited = set()
        
        for start in range(len(localities)):
            if start in visited:
                continue
            
            # BFS to find component
            component = []
            queue = [start]
            visited.add(start)
            
            while queue:
                current = queue.pop(0)
                component.append(current)
                
                for neighbor in adjacency[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            components.append(sorted(component))
        
        return components
    
    def analyze_topology(self, subnet: Subnet) -> Dict[str, Any]:
        """Analyze topological properties of subnet.
        
        Args:
            subnet: Subnet object
            
        Returns:
            Dict with topology metrics
        """
        return {
            'num_transitions': len(subnet.transitions),
            'num_places': len(subnet.places),
            'num_arcs': len(subnet.arcs),
            'num_boundary_places': len(subnet.boundary_places),
            'num_internal_places': len(subnet.internal_places),
            'num_dependencies': len(subnet.dependencies),
            'is_connected': len(subnet.dependencies) > 0,
            'boundary_ratio': len(subnet.boundary_places) / len(subnet.places) if subnet.places else 0
        }
