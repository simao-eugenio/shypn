"""Minimal per-document Undo/Redo manager.

Provides a lightweight stack-based undo system for canvas operations.
Each operation implements apply_undo(manager) and apply_redo(manager).

Lifecycle Integration:
- One UndoManager per ModelCanvasManager (created in _setup_canvas_manager)
- Shortcut wiring (Ctrl+Z / Ctrl+Y / Ctrl+Shift+Z) invokes undo/redo
- Operations pushed immediately after completion (e.g., MoveOperation after drag)
"""

from typing import List, Callable, Optional


class UndoManager:
	def __init__(self):
		self._undo_stack: List[object] = []
		self._redo_stack: List[object] = []
		self._state_cb: Optional[Callable[[bool, bool], None]] = None

	# ---- Public API ----
	def push(self, operation):
		"""Push a completed operation onto the undo stack and clear redo stack."""
		if operation is None:
			return
		self._undo_stack.append(operation)
		self._redo_stack.clear()
		self._emit_state()

	def undo(self, manager) -> bool:
		"""Undo the last operation.

		Returns True if an operation was undone.
		"""
		if not self._undo_stack:
			return False
		op = self._undo_stack.pop()
		try:
			op.apply_undo(manager)
			self._redo_stack.append(op)
			return True
		finally:
			self._emit_state()

	def redo(self, manager) -> bool:
		"""Redo the last undone operation.

		Returns True if an operation was redone.
		"""
		if not self._redo_stack:
			return False
		op = self._redo_stack.pop()
		try:
			op.apply_redo(manager)
			self._undo_stack.append(op)
			return True
		finally:
			self._emit_state()

	def can_undo(self) -> bool:
		return len(self._undo_stack) > 0

	def can_redo(self) -> bool:
		return len(self._redo_stack) > 0

	def clear(self):
		self._undo_stack.clear()
		self._redo_stack.clear()
		self._emit_state()

	def set_state_changed_callback(self, cb: Callable[[bool, bool], None]):
		self._state_cb = cb
		self._emit_state()

	# ---- Internal ----
	def _emit_state(self):
		if self._state_cb:
			try:
				self._state_cb(self.can_undo(), self.can_redo())
			except Exception:
				pass

