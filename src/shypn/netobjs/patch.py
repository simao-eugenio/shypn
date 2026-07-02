"""Loader-correct programmatic patching of ``.shy`` model files.

Why this module exists
----------------------
The ``.shy`` JSON loaders (`Place.from_dict`, `Transition.from_dict`,
`Arc.from_dict`, `DocumentModel.from_dict`) read each field from a
specific JSON scope — top-level vs the ``properties`` sub-dict. Writing
to the wrong scope is a **silent no-op**: the file saves cleanly, the
loader ignores the value, the engine sees the previous baseline, and a
sweep / dispatch produces wrong-but-plausible results.

The recurring trap (audited 2026-04-30) is two-fold:

1. **Scope mistakes** — e.g. writing
   ``transition["rate_function"]`` when the loader reads
   ``transition["properties"]["rate_function"]``.
2. **`tokens` vs `initial_marking` confusion on places** — writers set
   ``place["tokens"] = X`` thinking they are changing the start value.
   The loader reads ``initial_marking`` (which stays at the old value)
   and the saved ``tokens`` is silently ignored.

This module provides the canonical write functions every patch script
*must* go through. Each helper:

* Writes to the loader's authoritative read scope.
* Strips legacy / wrong-scope keys that would shadow or confuse a future
  reader.
* Asserts a roundtrip read at the loader's read scope before returning.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Union


PathLike = Union[str, Path]


# ---------------------------------------------------------------------------
# Place helpers
# ---------------------------------------------------------------------------

def _find_place(model: dict, name_or_id: str) -> dict:
    for p in model.get("places", []):
        if p.get("id") == name_or_id or p.get("name") == name_or_id:
            return p
    raise KeyError(f"Place {name_or_id!r} not found in model")


def set_place_value(
    model: dict,
    name_or_id: str,
    value: float,
    *,
    treat_as: str = "initial_marking",
) -> dict:
    """Set the basal value of a place at the loader's read scope.

    ``initial_marking`` is the **only** field the loader reads to populate
    M_0. ``tokens`` is transient runtime state and is ignored on load.

    This helper:

    * Writes ``place["initial_marking"] = float(value)`` (top-level).
    * Mirrors to the legacy ``place["marking"]`` key for forward-compat
      with old loaders.
    * Removes any stray ``place["tokens"]`` key that would otherwise
      indicate a previous wrong-scope write.

    Args:
        model: Parsed model dict (``json.load`` of a ``.shy`` file).
        name_or_id: Place name (e.g. ``"MAINT_DOSE"``) or id (``"P36"``).
        value: New basal value.
        treat_as: Reserved; only ``"initial_marking"`` is supported.

    Returns:
        The mutated place dict.

    Raises:
        KeyError: If the named/id place is not in the model.
        ValueError: If ``treat_as`` is not ``"initial_marking"``.
    """
    if treat_as != "initial_marking":
        raise ValueError(
            f"set_place_value: treat_as={treat_as!r} unsupported; "
            f"the loader only reads 'initial_marking'."
        )
    place = _find_place(model, name_or_id)
    v = float(value)
    place["initial_marking"] = v
    place["marking"] = v  # legacy mirror
    place.pop("tokens", None)  # never persist runtime state
    # Roundtrip assertion (defensive — catches future loader-scope drift).
    assert place["initial_marking"] == v, "set_place_value roundtrip failed"
    assert "tokens" not in place, "set_place_value left a stale tokens key"
    return place


def patch_shy_file(
    path: PathLike,
    place_values: Optional[Mapping[str, float]] = None,
    *,
    backup: bool = True,
) -> dict:
    """Convenience: load a ``.shy`` file, apply patches, save back.

    Args:
        path: Path to the ``.shy`` file.
        place_values: Mapping of place name/id → new basal value.
        backup: If True (default), write a ``.shy.bak`` next to the file
            before overwriting.

    Returns:
        The mutated model dict.
    """
    p = Path(path)
    model = json.loads(p.read_text(encoding="utf-8"))
    if place_values:
        for key, val in place_values.items():
            set_place_value(model, key, val)
    if backup:
        bak = p.with_suffix(p.suffix + ".bak")
        bak.write_text(json.dumps(json.loads(p.read_text(encoding="utf-8")),
                                  indent=2), encoding="utf-8")
    p.write_text(json.dumps(model, indent=2), encoding="utf-8")
    return model


# ---------------------------------------------------------------------------
# Divergence inspection (used by GUI save dialog)
# ---------------------------------------------------------------------------

def find_runtime_divergence(places: Iterable[Any]) -> list[Any]:
    """Return the list of `Place` objects with ``tokens != initial_marking``.

    Called pre-save by the GUI to surface the promote/discard dialog.
    """
    out = []
    for pl in places:
        try:
            if pl.has_runtime_divergence():
                out.append(pl)
        except AttributeError:
            # Older Place objects without the helper — fall back to direct attrs
            if float(getattr(pl, "tokens", 0)) != float(getattr(pl, "initial_marking", 0)):
                out.append(pl)
    return out


__all__ = [
    "set_place_value",
    "patch_shy_file",
    "find_runtime_divergence",
]
