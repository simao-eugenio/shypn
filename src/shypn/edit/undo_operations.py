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
	"""Stub DeleteOperation (not yet wired).

	Would store snapshots of deleted objects; undo re-adds them, redo deletes again.
	"""
	def __init__(self, snapshots: List[dict]):
		self.snapshots = snapshots

	def apply_undo(self, manager):
		# TODO: reconstruct objects from snapshots
		pass

	def apply_redo(self, manager):
		# TODO: delete again
		pass

