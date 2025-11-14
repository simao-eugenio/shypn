"""Basic undo operation types.

Currently implements MoveOperation for object position changes.
DeleteOperation stub included for future expansion.
"""

from typing import Dict, Tuple, List


class MoveOperation:
	"""Represents a move (drag) of one or more objects.

	Stores initial and final (x, y) positions keyed by Python id(obj).
	"""
	def __init__(self, initial_positions: Dict[int, Tuple[float, float]], manager):
		# Capture final positions at construction time
		self.initial = dict(initial_positions)
		self.final: Dict[int, Tuple[float, float]] = {}
		# Build final positions from current object states in manager
		for obj in manager.get_all_objects():
			obj_id = id(obj)
			if obj_id in self.initial:
				# Assume objects have x,y
				self.final[obj_id] = (getattr(obj, 'x', 0.0), getattr(obj, 'y', 0.0))

	def apply_undo(self, manager):
		for obj in manager.get_all_objects():
			obj_id = id(obj)
			if obj_id in self.initial:
				x, y = self.initial[obj_id]
				if hasattr(obj, 'x') and hasattr(obj, 'y'):
					obj.x = x
					obj.y = y
		manager.mark_needs_redraw()

	def apply_redo(self, manager):
		for obj in manager.get_all_objects():
			obj_id = id(obj)
			if obj_id in self.final:
				x, y = self.final[obj_id]
				if hasattr(obj, 'x') and hasattr(obj, 'y'):
					obj.x = x
					obj.y = y
		manager.mark_needs_redraw()


class DeleteOperation:
	"""Undoable delete operation.

	Stores snapshot dicts (see snapshots.capture_delete_snapshots) for objects
	and incident arcs removed in a delete action. Undo recreates the objects and
	associated arcs. Redo deletes them again.
	"""
	def __init__(self, snapshots: List[dict]):
		# Defensive copy
		self.snapshots = [dict(s) for s in snapshots]

	def apply_undo(self, manager):
		"""Recreate deleted objects and arcs.

		Order matters: create places/transitions first, then arcs referencing them.
		We bypass ID generation to preserve original IDs, assuming no conflicts.
		"""
		from shypn.core.model.place import Place  # local imports to avoid cycles
		from shypn.core.model.transition import Transition
		from shypn.core.model.arc import Arc

		dc = manager.document_controller

		# Build lookup to avoid duplicates if multiple snapshots reference same arc
		pending_arcs: List[dict] = []

		for snap in self.snapshots:
			kind = snap.get('kind')
			if kind == 'arc':
				pending_arcs.append(snap)
				continue
			if kind == 'place':
				obj = Place(snap.get('x', 0.0), snap.get('y', 0.0), snap.get('id'), snap.get('label'), radius=snap.get('radius'))
				dc.places.append(obj)
			elif kind == 'transition':
				obj = Transition(snap.get('x', 0.0), snap.get('y', 0.0), snap.get('id'), snap.get('label'), width=snap.get('width'), height=snap.get('height'))
				dc.transitions.append(obj)
			# inline arcs for place/transition
			for arc_snap in snap.get('arcs', []):
				pending_arcs.append(arc_snap)

		# Build mapping from ID to object for endpoint resolution
		id_map = {getattr(p, 'id'): p for p in dc.places}
		id_map.update({getattr(t, 'id'): t for t in dc.transitions})

		# Create arcs
		for a in pending_arcs:
			if any(existing.id == a.get('id') for existing in dc.arcs):
				continue  # skip if already present
			source = id_map.get(a.get('source_id'))
			target = id_map.get(a.get('target_id'))
			if source and target:
				arc = Arc(source, target, a.get('id'), a.get('label'))
				dc.arcs.append(arc)

		manager.mark_needs_redraw()

	def apply_redo(self, manager):
		"""Delete the objects again using snapshot IDs.

		We remove arcs first, then places/transitions to mirror cascade behavior.
		"""
		dc = manager.document_controller
		# Remove arcs by id
		arc_ids = {snap.get('id') for snap in self.snapshots if snap.get('kind') == 'arc'}
		for snap in self.snapshots:
			if snap.get('kind') in ('place', 'transition'):
				for arc_snap in snap.get('arcs', []):
					arc_ids.add(arc_snap.get('id'))
		dc.arcs = [a for a in dc.arcs if getattr(a, 'id', None) not in arc_ids]

		# Remove places/transitions
		place_ids = {snap.get('id') for snap in self.snapshots if snap.get('kind') == 'place'}
		transition_ids = {snap.get('id') for snap in self.snapshots if snap.get('kind') == 'transition'}
		dc.places = [p for p in dc.places if getattr(p, 'id', None) not in place_ids]
		dc.transitions = [t for t in dc.transitions if getattr(t, 'id', None) not in transition_ids]

		manager.mark_needs_redraw()

