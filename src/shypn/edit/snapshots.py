"""Snapshot helpers for undoable delete operations.

Provides `capture_delete_snapshots(manager, objects)` which collects sufficient
data to recreate deleted objects (places, transitions, arcs) together with
their directly connected arcs. Designed to support cascade deletes: deleting a
place or transition also removes its incident arcs; deleting an arc only
captures that arc.

We intentionally keep the snapshot structure simple (JSON-friendly dicts) to
allow future persistence or multi-level undo grouping.

Snapshot format (list of dicts):
[
  {
	'kind': 'place' | 'transition' | 'arc',
	'id': <string>,
	'label': <string or None>,
	'x': <float>, 'y': <float>,              # for place/transition
	'radius': <float?>,                      # optional place attr
	'width': <float?>, 'height': <float?>,   # optional transition attrs
	'source_id': <string>, 'target_id': <string>,  # for arc
	'connected_arc_ids': [<arc_id>, ...]     # only for place/transition
	'arcs': [ { 'id':..., 'label':..., 'source_id':..., 'target_id':... }, ... ]  # inline arc snapshots (place/transition)
  },
  ...
]

For places/transitions we inline their incident arcs to ensure redo deletion
and undo recreation remain deterministic even if other operations occur in
between.
"""

from typing import List, Dict, Any, Set


def capture_delete_snapshots(manager, objects: List[object]) -> List[Dict[str, Any]]:
	"""Capture snapshot data for objects about to be deleted.

	Args:
		manager: The `ModelCanvasManager` instance orchestrating the document.
		objects: List of objects (Place, Transition, Arc) slated for deletion.

	Returns:
		List of snapshot dicts (see module docstring for structure).
	"""
	snapshots: List[Dict[str, Any]] = []
	recorded_arc_ids: Set[str] = set()

	# Helper to snapshot an arc (avoids duplication)
	def snapshot_arc(arc) -> Dict[str, Any]:
		return {
			'kind': 'arc',
			'id': getattr(arc, 'id', None),
			'label': getattr(arc, 'label', None),
			'source_id': getattr(arc.source, 'id', None),
			'target_id': getattr(arc.target, 'id', None),
		}

	# Collect object type names (simplistic classification)
	for obj in objects:
		kind = _classify_kind(obj)
		if kind == 'arc':
			# Simple arc snapshot
			arc_snap = snapshot_arc(obj)
			if arc_snap['id'] and arc_snap['id'] not in recorded_arc_ids:
				snapshots.append(arc_snap)
				recorded_arc_ids.add(arc_snap['id'])
			continue

		# Place or Transition: capture geometry & label
		base = {
			'kind': kind,
			'id': getattr(obj, 'id', None),
			'label': getattr(obj, 'label', None),
			'x': getattr(obj, 'x', 0.0),
			'y': getattr(obj, 'y', 0.0),
		}
		if kind == 'place':
			base['radius'] = getattr(obj, 'radius', None)
		elif kind == 'transition':
			base['width'] = getattr(obj, 'width', None)
			base['height'] = getattr(obj, 'height', None)

		# Incident arcs
		incident_arc_snaps: List[Dict[str, Any]] = []
		connected_ids: List[str] = []
		for arc in manager.document_controller.arcs:
			if getattr(arc, 'source', None) == obj or getattr(arc, 'target', None) == obj:
				arc_id = getattr(arc, 'id', None)
				if arc_id and arc_id not in recorded_arc_ids:
					arc_snap = snapshot_arc(arc)
					incident_arc_snaps.append(arc_snap)
					recorded_arc_ids.add(arc_id)
					connected_ids.append(arc_id)

		base['connected_arc_ids'] = connected_ids
		base['arcs'] = incident_arc_snaps
		snapshots.append(base)

	return snapshots


def _classify_kind(obj: object) -> str:
	name = obj.__class__.__name__.lower()
	if 'arc' in name:
		return 'arc'
	if 'transition' in name:
		return 'transition'
	return 'place'  # default assumption

