"""
Snapshot Utility Functions

This module provides functions to:
1. Capture complete object state (snapshot)
2. Recreate objects from snapshots
3. Remove objects by ID or snapshot
4. Find objects for reconnection

Used by undo/redo operations to preserve and restore object state.
"""

from typing import Dict, Any, Optional


def snapshot_place(place) -> Dict[str, Any]:
    """
    Capture complete state of a place for undo/redo.
    
    Args:
        place: Place object to snapshot
        
    Returns:
        Dictionary with all place properties
    """
    return {
        'type': 'place',
        'id': place.id,
        'name': place.name,
        'x': place.x,
        'y': place.y,
        'radius': place.radius,
        'tokens': place.tokens,
        'marking': getattr(place, 'marking', place.tokens),
        'capacity': getattr(place, 'capacity', float('inf')),
        'properties': dict(place.properties) if hasattr(place, 'properties') else {}
    }


def snapshot_transition(transition) -> Dict[str, Any]:
    """
    Capture complete state of a transition for undo/redo.
    
    Args:
        transition: Transition object to snapshot
        
    Returns:
        Dictionary with all transition properties
    """
    snapshot = {
        'type': 'transition',
        'id': transition.id,
        'name': transition.name,
        'x': transition.x,
        'y': transition.y,
        'width': transition.width,
        'height': transition.height,
        'horizontal': transition.horizontal,
        'transition_type': getattr(transition, 'transition_type', 'immediate'),
        'properties': dict(transition.properties) if hasattr(transition, 'properties') else {}
    }
    
    # Capture type-specific properties
    if hasattr(transition, 'rate'):
        snapshot['rate'] = transition.rate
    if hasattr(transition, 'delay'):
        snapshot['delay'] = transition.delay
    if hasattr(transition, 'weight'):
        snapshot['weight'] = transition.weight
    
    return snapshot


def snapshot_arc(arc) -> Dict[str, Any]:
    """
    Capture complete state of an arc for undo/redo.
    
    Args:
        arc: Arc object to snapshot
        
    Returns:
        Dictionary with all arc properties including source/target IDs
    """
    # Determine source type and ID
    if hasattr(arc.source, 'id'):
        source_id = arc.source.id
        # Check if it's a place or transition
        source_type = 'place' if 'Place' in type(arc.source).__name__ else 'transition'
    else:
        # Fallback
        source_type = 'place'
        source_id = 0
    
    # Determine target type and ID
    if hasattr(arc.target, 'id'):
        target_id = arc.target.id
        # Check if it's a place or transition  
        target_type = 'place' if 'Place' in type(arc.target).__name__ else 'transition'
    else:
        # Fallback
        target_type = 'place'
        target_id = 0
    
    return {
        'type': 'arc',
        'id': arc.id,
        'name': arc.name,
        'source_id': source_id,
        'target_id': target_id,
        'source_type': source_type,
        'target_type': target_type,
        'weight': arc.weight,
        'arc_kind': getattr(arc, 'arc_kind', 'normal'),
        'properties': dict(arc.properties) if hasattr(arc, 'properties') else {}
    }


def recreate_place(canvas_manager, snapshot: Dict[str, Any]):
    """
    Recreate a place from a snapshot.
    
    Args:
        canvas_manager: ModelCanvasManager instance
        snapshot: Place snapshot from snapshot_place()
    """
    from shypn.netobjs.place import Place
    
    place = Place(
        x=snapshot['x'],
        y=snapshot['y'],
        id=snapshot['id'],
        name=snapshot['name'],
        radius=snapshot['radius']
    )
    place.tokens = snapshot['tokens']
    place.initial_marking = snapshot.get('marking', snapshot['tokens'])
    
    if snapshot.get('properties'):
        if not hasattr(place, 'properties'):
            place.properties = {}
        place.properties.update(snapshot['properties'])
    
    canvas_manager.places.append(place)
    
    # Update ID counter if necessary
    if snapshot['id'] >= canvas_manager._next_place_id:
        canvas_manager._next_place_id = snapshot['id'] + 1


def recreate_transition(canvas_manager, snapshot: Dict[str, Any]):
    """
    Recreate a transition from a snapshot.
    
    Args:
        canvas_manager: ModelCanvasManager instance
        snapshot: Transition snapshot from snapshot_transition()
    """
    from shypn.netobjs.transition import Transition
    
    transition = Transition(
        x=snapshot['x'],
        y=snapshot['y'],
        id=snapshot['id'],
        name=snapshot['name'],
        width=snapshot['width'],
        height=snapshot['height'],
        horizontal=snapshot['horizontal']
    )
    transition.transition_type = snapshot.get('transition_type', 'immediate')
    
    # Restore type-specific properties
    if 'rate' in snapshot:
        transition.rate = snapshot['rate']
    if 'delay' in snapshot:
        transition.delay = snapshot['delay']
    if 'weight' in snapshot:
        transition.weight = snapshot['weight']
    
    if snapshot.get('properties'):
        if not hasattr(transition, 'properties'):
            transition.properties = {}
        transition.properties.update(snapshot['properties'])
    
    canvas_manager.transitions.append(transition)
    
    # Update ID counter if necessary
    if snapshot['id'] >= canvas_manager._next_transition_id:
        canvas_manager._next_transition_id = snapshot['id'] + 1


def recreate_arc(canvas_manager, snapshot: Dict[str, Any]):
    """
    Recreate an arc from a snapshot.
    
    Args:
        canvas_manager: ModelCanvasManager instance
        snapshot: Arc snapshot from snapshot_arc()
    """
    from shypn.netobjs.arc import Arc
    
    # Find source object
    if snapshot['source_type'] == 'place':
        source = next((p for p in canvas_manager.places if p.id == snapshot['source_id']), None)
    else:
        source = next((t for t in canvas_manager.transitions if t.id == snapshot['source_id']), None)
    
    # Find target object
    if snapshot['target_type'] == 'place':
        target = next((p for p in canvas_manager.places if p.id == snapshot['target_id']), None)
    else:
        target = next((t for t in canvas_manager.transitions if t.id == snapshot['target_id']), None)
    
    if not source or not target:
        return
    
    arc = Arc(
        source=source,
        target=target,
        id=snapshot['id'],
        name=snapshot['name'],
        weight=snapshot['weight']
    )
    arc.arc_kind = snapshot.get('arc_kind', 'normal')
    
    if snapshot.get('properties'):
        if not hasattr(arc, 'properties'):
            arc.properties = {}
        arc.properties.update(snapshot['properties'])
    
    canvas_manager.arcs.append(arc)
    
    # Update ID counter if necessary
    if snapshot['id'] >= canvas_manager._next_arc_id:
        canvas_manager._next_arc_id = snapshot['id'] + 1


def recreate_from_snapshot(canvas_manager, snapshot: Dict[str, Any]):
    """
    Recreate any object from its snapshot.
    
    Args:
        canvas_manager: ModelCanvasManager instance
        snapshot: Object snapshot (place, transition, or arc)
    """
    obj_type = snapshot['type']
    
    if obj_type == 'place':
        recreate_place(canvas_manager, snapshot)
    elif obj_type == 'transition':
        recreate_transition(canvas_manager, snapshot)
    elif obj_type == 'arc':
        recreate_arc(canvas_manager, snapshot)
    else:


def remove_place_by_id(canvas_manager, place_id: int):
    """
    Remove a place by its ID.
    
    Args:
        canvas_manager: ModelCanvasManager instance
        place_id: ID of place to remove
    """
    canvas_manager.places = [p for p in canvas_manager.places if p.id != place_id]


def remove_transition_by_id(canvas_manager, transition_id: int):
    """
    Remove a transition by its ID.
    
    Args:
        canvas_manager: ModelCanvasManager instance
        transition_id: ID of transition to remove
    """
    canvas_manager.transitions = [t for t in canvas_manager.transitions if t.id != transition_id]


def remove_arc_by_id(canvas_manager, arc_id: int):
    """
    Remove an arc by its ID.
    
    Args:
        canvas_manager: ModelCanvasManager instance
        arc_id: ID of arc to remove
    """
    canvas_manager.arcs = [a for a in canvas_manager.arcs if a.id != arc_id]


def remove_object_by_snapshot(canvas_manager, snapshot: Dict[str, Any]):
    """
    Remove an object using its snapshot.
    
    Args:
        canvas_manager: ModelCanvasManager instance
        snapshot: Object snapshot (place, transition, or arc)
    """
    obj_type = snapshot['type']
    obj_id = snapshot['id']
    
    if obj_type == 'place':
        remove_place_by_id(canvas_manager, obj_id)
    elif obj_type == 'transition':
        remove_transition_by_id(canvas_manager, obj_id)
    elif obj_type == 'arc':
        remove_arc_by_id(canvas_manager, obj_id)


def capture_delete_snapshots(canvas_manager, objects_to_delete: list) -> list:
    """
    Capture snapshots for objects about to be deleted, including connected arcs.
    
    Args:
        canvas_manager: ModelCanvasManager instance
        objects_to_delete: List of objects to delete (places, transitions)
        
    Returns:
        List of snapshots for all objects to be deleted (including arcs)
    """
    snapshots = []
    deleted_ids = {'places': set(), 'transitions': set()}
    
    # Snapshot the objects themselves
    for obj in objects_to_delete:
        # Check if it's a Place
        if 'Place' in type(obj).__name__:
            snapshots.append(snapshot_place(obj))
            deleted_ids['places'].add(obj.id)
        # Check if it's a Transition
        elif 'Transition' in type(obj).__name__:
            snapshots.append(snapshot_transition(obj))
            deleted_ids['transitions'].add(obj.id)
    
    # Find and snapshot connected arcs
    for arc in canvas_manager.arcs:
        arc_should_be_deleted = False
        
        # Check if arc's source is being deleted
        source_type = 'place' if 'Place' in type(arc.source).__name__ else 'transition'
        if source_type == 'place' and arc.source.id in deleted_ids['places']:
            arc_should_be_deleted = True
        elif source_type == 'transition' and arc.source.id in deleted_ids['transitions']:
            arc_should_be_deleted = True
        
        # Check if arc's target is being deleted
        target_type = 'place' if 'Place' in type(arc.target).__name__ else 'transition'
        if target_type == 'place' and arc.target.id in deleted_ids['places']:
            arc_should_be_deleted = True
        elif target_type == 'transition' and arc.target.id in deleted_ids['transitions']:
            arc_should_be_deleted = True
        
        if arc_should_be_deleted:
            snapshots.append(snapshot_arc(arc))
    
    return snapshots
