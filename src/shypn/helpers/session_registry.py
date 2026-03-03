"""SessionRegistry — single source of truth for all per-document components.

Sprint 18 — Phase 7: replaces the four parallel legacy dicts
(``canvas_managers``, ``overlay_managers``, ``simulation_controllers``,
``knowledge_bases``) that used to live in ``ModelCanvasLoader``.

Usage
-----
``ModelCanvasLoader.__init__`` creates one :class:`SessionRegistry` and
exposes its four live proxy attributes so that **all existing external callers**
continue to work without any changes::

    self._registry             = SessionRegistry()
    self.sessions              = self._registry          # dict-like view of sessions
    self.canvas_managers       = self._registry.proxy("canvas_manager")
    self.overlay_managers      = self._registry.proxy("overlay_manager")
    self.simulation_controllers = self._registry.proxy("simulation_controller")
    self.knowledge_bases       = self._registry.proxy("knowledge_base")

The proxy objects are regular Python objects whose ``__getitem__``,
``__setitem__``, ``__contains__``, ``get``, ``items``, ``keys`` all delegate
live reads/writes to the underlying :class:`~shypn.helpers.document_session.DocumentSession`
field of that name.  The :func:`del proxy[da]` operation is intentionally a
no-op because the canonical removal path is :meth:`SessionRegistry.pop`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterator, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from shypn.helpers.document_session import DocumentSession

logger = logging.getLogger(__name__)

__all__ = ["SessionRegistry", "_SessionFieldProxy"]


# ---------------------------------------------------------------------------
# Live field proxy
# ---------------------------------------------------------------------------

class _SessionFieldProxy:
    """Dict-like live view that reads/writes one field on every
    :class:`~shypn.helpers.document_session.DocumentSession` stored in a
    :class:`SessionRegistry`.

    This is *not* a copy — writes go directly to the session object so that
    all readers (including external panels) always see the current value.

    Parameters
    ----------
    registry:
        The owning :class:`SessionRegistry`.
    field:
        The :class:`~shypn.helpers.document_session.DocumentSession` slot
        name to proxy (e.g. ``"canvas_manager"``).
    """

    __slots__ = ("_registry", "_field")

    def __init__(self, registry: "SessionRegistry", field: str) -> None:
        self._registry = registry
        self._field = field

    # --- read access --------------------------------------------------

    def get(self, key: Any, default: Any = None) -> Any:
        """Return the component for *key*, or *default* if not registered."""
        session: Optional["DocumentSession"] = self._registry._sessions.get(key)
        if session is None:
            return default
        return getattr(session, self._field, default)

    def __getitem__(self, key: Any) -> Any:
        session: Optional["DocumentSession"] = self._registry._sessions.get(key)
        if session is None:
            raise KeyError(key)
        return getattr(session, self._field)

    def __contains__(self, key: Any) -> bool:
        return key in self._registry._sessions

    def __iter__(self) -> Iterator[Any]:
        return iter(self._registry._sessions)

    def keys(self) -> Any:
        return self._registry._sessions.keys()

    def items(self) -> Iterator[Tuple[Any, Any]]:
        """Yield ``(drawing_area, component)`` pairs."""
        field = self._field
        for da, session in self._registry._sessions.items():
            yield da, getattr(session, field)

    # --- write access -------------------------------------------------

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set the component on an already-registered session.

        If no session exists yet for *key* a :class:`KeyError` is raised to
        surface the ordering bug early rather than silently losing the write.
        """
        session: Optional["DocumentSession"] = self._registry._sessions.get(key)
        if session is None:
            raise KeyError(
                f"_SessionFieldProxy[{self._field!r}]: no session registered "
                f"for key {key!r} — create the DocumentSession first."
            )
        setattr(session, self._field, value)

    def __delitem__(self, key: Any) -> None:
        # Intentional no-op: canonical removal is SessionRegistry.pop().
        # Legacy close_tab code still calls `del self.canvas_managers[da]` etc.;
        # those calls are harmless after Sprint 18 and will be cleaned up in a
        # future sprint.
        pass

    def __repr__(self) -> str:  # pragma: no cover
        n = len(self._registry._sessions)
        return f"_SessionFieldProxy(field={self._field!r}, sessions={n})"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class SessionRegistry:
    """Single source of truth for all per-document components.

    Wraps ``dict[drawing_area → DocumentSession]`` and exposes four typed
    proxy attributes so that the legacy ``canvas_managers`` etc. dict API
    continues to work transparently via :class:`_SessionFieldProxy`.

    Typical lifecycle
    -----------------
    1. :meth:`register` — called once ``canvas_manager``, ``overlay_manager``,
       ``knowledge_base`` are known.  ``simulation_controller`` may be ``None``
       at that point and filled in later via the ``simulation_controllers``
       proxy.
    2. :meth:`get` / subscript / proxy attributes — component lookups.
    3. :meth:`pop` — removes and returns the session during tab close so
       ``DocumentSession.teardown()`` can be called.
    """

    def __init__(self) -> None:
        self._sessions: Dict[Any, "DocumentSession"] = {}

        # Typed live-proxy views — assign to MCL attributes so external code
        # continues to work without modification.
        self.canvas_managers: _SessionFieldProxy = _SessionFieldProxy(self, "canvas_manager")
        self.overlay_managers: _SessionFieldProxy = _SessionFieldProxy(self, "overlay_manager")
        self.simulation_controllers: _SessionFieldProxy = _SessionFieldProxy(self, "simulation_controller")
        self.knowledge_bases: _SessionFieldProxy = _SessionFieldProxy(self, "knowledge_base")

    # --- session-level operations ------------------------------------

    def register(self, drawing_area: Any, session: "DocumentSession") -> None:
        """Store *session* keyed by *drawing_area*.

        Overwrites any existing session for that key (re-registration is
        silently accepted for hot-reload scenarios).
        """
        self._sessions[drawing_area] = session
        logger.debug(
            "SessionRegistry.register(): doc_id=%d drawing_area=%s",
            session.doc_id,
            drawing_area,
        )

    def pop(self, drawing_area: Any, default: Any = None) -> "Optional[DocumentSession]":
        """Remove and return the session for *drawing_area*.

        Returns *default* if the key is not present (matching ``dict.pop``
        semantics).
        """
        session = self._sessions.pop(drawing_area, default)
        if session is not None and session is not default:
            logger.debug(
                "SessionRegistry.pop(): removed doc_id=%d drawing_area=%s",
                session.doc_id,
                drawing_area,
            )
        return session

    def get(self, drawing_area: Any, default: Any = None) -> "Optional[DocumentSession]":
        """Return the session for *drawing_area*, or *default*."""
        return self._sessions.get(drawing_area, default)

    # --- dict-compatible helpers used by MCL's sessions attribute ----

    def __getitem__(self, key: Any) -> "DocumentSession":
        return self._sessions[key]

    def __setitem__(self, key: Any, value: "DocumentSession") -> None:
        self.register(key, value)

    def __delitem__(self, key: Any) -> None:
        self._sessions.pop(key, None)

    def __contains__(self, key: Any) -> bool:
        return key in self._sessions

    def __iter__(self) -> Iterator[Any]:
        return iter(self._sessions)

    def __len__(self) -> int:
        return len(self._sessions)

    def items(self) -> Any:
        return self._sessions.items()

    def keys(self) -> Any:
        return self._sessions.keys()

    def values(self) -> Any:
        return self._sessions.values()

    def __repr__(self) -> str:  # pragma: no cover
        return f"SessionRegistry(sessions={len(self._sessions)})"
