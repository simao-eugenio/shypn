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
	associated arcs with original IDs; redo deletes them again using facade
	methods to ensure cascade + observers.
	"""
	def __init__(self, snapshots: List[dict]):
		self.snapshots = [dict(s) for s in snapshots]

	def apply_undo(self, manager):
		"""Recreate deleted objects and arcs in a safe order.

		Implementation details:
		- Create Places & Transitions first (manual instantiation preserves IDs)
		- Register their IDs with the IDManager to avoid future collisions
		- Recreate Arcs referencing restored endpoints
		- Notify observers & mark document dirty/redraw
		"""
		from shypn.netobjs import Place, Transition, Arc
		dc = manager.document_controller

		pending_arc_snaps: List[dict] = []
		created_nodes = []

		for snap in self.snapshots:
			kind = snap.get('kind')
			if kind == 'arc':
				pending_arc_snaps.append(snap)
				continue
			if kind == 'place':
				obj = Place(snap.get('x', 0.0), snap.get('y', 0.0), snap.get('id'), snap.get('label'), radius=snap.get('radius'))
				dc.places.append(obj)
				created_nodes.append(obj)
			elif kind == 'transition':
				obj = Transition(snap.get('x', 0.0), snap.get('y', 0.0), snap.get('id'), snap.get('label'), width=snap.get('width'), height=snap.get('height'))
				dc.transitions.append(obj)
				created_nodes.append(obj)
			for arc_snap in snap.get('arcs', []):
				pending_arc_snaps.append(arc_snap)

		# Register IDs for nodes
		for n in created_nodes:
			if hasattr(n, 'id'):
				if 'P' in n.id:
					dc.id_manager.register_place_id(n.id)
				elif 'T' in n.id:
					dc.id_manager.register_transition_id(n.id)

		# Build mapping for endpoints
		id_map = {getattr(p, 'id'): p for p in dc.places}
		id_map.update({getattr(t, 'id'): t for t in dc.transitions})

		created_arcs = []
		for arc_snap in pending_arc_snaps:
			arc_id = arc_snap.get('id')
			if any(getattr(existing, 'id', None) == arc_id for existing in dc.arcs):
				continue
			source = id_map.get(arc_snap.get('source_id'))
			target = id_map.get(arc_snap.get('target_id'))
			if source and target:
				arc = Arc(source, target, arc_id, arc_snap.get('label'))
				dc.arcs.append(arc)
				created_arcs.append(arc)
				if arc_id and 'A' in arc_id:
					dc.id_manager.register_arc_id(arc_id)

		# Observer notifications (facade-level)
		for obj in created_nodes + created_arcs:
			try:
				manager._notify_observers('created', obj)
			except Exception:
				pass

		# Mark dirty & redraw
		manager.mark_dirty()
		manager.mark_needs_redraw()

	def apply_redo(self, manager):
		"""Delete the objects again via facade cascade methods."""
		from shypn.netobjs import Place, Transition, Arc
		# Delete nodes first (cascade removes attached arcs) then standalone arcs
		# Collect node IDs to delete
		place_ids = {s.get('id') for s in self.snapshots if s.get('kind') == 'place'}
		transition_ids = {s.get('id') for s in self.snapshots if s.get('kind') == 'transition'}
		arc_ids = [s.get('id') for s in self.snapshots if s.get('kind') == 'arc']

		# Helper to find by id
		def _find(seq, obj_id):
			for o in seq:
				if getattr(o, 'id', None) == obj_id:
					return o
			return None

		for pid in place_ids:
			p = _find(manager.places, pid)
			if p:
				manager.remove_place(p)

		for tid in transition_ids:
			t = _find(manager.transitions, tid)
			if t:
				manager.remove_transition(t)

		# Remaining arcs (that were standalone deletions originally)
		for aid in arc_ids:
			arc = _find(manager.arcs, aid)
			if arc:
				manager.remove_arc(arc)

		manager.mark_dirty()
		manager.mark_needs_redraw()

