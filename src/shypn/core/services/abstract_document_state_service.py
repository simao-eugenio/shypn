"""AbstractDocumentStateService — ABC for per-document dirty/filepath state.

Sprint 19 — Phase 7: defines the typed contract for all document state
operations extracted from ``ModelCanvasManager``.

Concrete implementation: :class:`~shypn.core.services.document_state_service.DocumentStateService`
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Optional

__all__ = ["AbstractDocumentStateService"]


class AbstractDocumentStateService(ABC):
    """Typed contract for per-document dirty, filepath, and import state.

    Implementations encapsulate:
    * unsaved-changes tracking (``_is_dirty`` flag + UI callback)
    * file path / filename bookkeeping
    * import/default-name detection

    All methods are called on the *hot path* (every model mutation) so
    implementations should guard against redundant state changes.
    """

    # ------------------------------------------------------------------
    # Dirty state
    # ------------------------------------------------------------------

    @abstractmethod
    def mark_dirty(self) -> None:
        """Mark document as having unsaved changes.

        Should fire ``on_dirty_changed(True)`` exactly once when the state
        transitions from clean → dirty (idempotent if already dirty).
        Must not fire while ``suppress_callbacks`` is ``True``.
        """

    @abstractmethod
    def mark_clean(self) -> None:
        """Mark document as clean (all changes saved).

        Should fire ``on_dirty_changed(False)`` when transitioning dirty →
        clean.  Must not fire while ``suppress_callbacks`` is ``True``.
        """

    @property
    @abstractmethod
    def is_dirty(self) -> bool:
        """``True`` when the document has unsaved changes."""

    # ------------------------------------------------------------------
    # Modification timestamps / modified flag
    # ------------------------------------------------------------------

    @abstractmethod
    def mark_modified(self) -> None:
        """Stamp the modification time and set the ``modified`` flag."""

    @abstractmethod
    def mark_as_saved(self) -> None:
        """Clear the imported flag after a successful save."""

    @abstractmethod
    def mark_as_imported(self, imported_name: Optional[str] = None) -> None:
        """Flag the document as imported (triggers save-as on first save)."""

    # ------------------------------------------------------------------
    # Filename / filepath
    # ------------------------------------------------------------------

    @abstractmethod
    def set_filename(self, filename: str) -> None:
        """Set the base filename (without path, without extension)."""

    @property
    @abstractmethod
    def filename(self) -> str:
        """Base filename without path."""

    @abstractmethod
    def is_default_filename(self) -> bool:
        """``True`` for new/imported documents that have never been saved."""

    @abstractmethod
    def set_filepath(self, filepath: str) -> None:
        """Set the full file path; also updates the base filename."""

    @property
    @abstractmethod
    def filepath(self) -> Optional[str]:
        """Absolute path to the saved file, or ``None`` for unsaved docs."""

    @abstractmethod
    def has_filepath(self) -> bool:
        """``True`` when the document has a valid saved filepath."""

    @abstractmethod
    def get_display_name(self) -> str:
        """Human-readable name for tab labels and window titles."""

    # ------------------------------------------------------------------
    # Callback / suppression control
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def on_dirty_changed(self) -> Optional[Callable[[bool], None]]:
        """Callback invoked when dirty state changes; may be ``None``."""

    @on_dirty_changed.setter
    @abstractmethod
    def on_dirty_changed(self, callback: Optional[Callable[[bool], None]]) -> None:
        """Set or replace the dirty-state callback."""

    @property
    @abstractmethod
    def suppress_callbacks(self) -> bool:
        """When ``True``, dirty-state callbacks are temporarily suppressed."""

    @suppress_callbacks.setter
    @abstractmethod
    def suppress_callbacks(self, value: bool) -> None:
        """Enable or disable callback suppression."""
