"""DocumentStateService — concrete per-document dirty/filepath state service.

Sprint 19 — Phase 7: implementation of
:class:`~shypn.core.services.abstract_document_state_service.AbstractDocumentStateService`
extracted from ``ModelCanvasManager``.

Usage (inside ModelCanvasManager.__init__ / create_new_document)::

    from shypn.core.services.document_state_service import DocumentStateService
    self._state_svc = DocumentStateService()
    self._state_svc.on_dirty_changed = my_callback

All public state methods on ModelCanvasManager now delegate here.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Callable, Optional

from shypn.core.services.abstract_document_state_service import AbstractDocumentStateService

__all__ = ["DocumentStateService"]

logger = logging.getLogger(__name__)


class DocumentStateService(AbstractDocumentStateService):
    """Owns dirty flag, filepath, filename and import state for one document.

    Designed for direct composition inside :class:`ModelCanvasManager`:
    the manager delegates all state methods to a single instance of this
    class so that state logic is testable without a full canvas.

    Thread safety: all callback dispatches happen synchronously on the
    calling thread (GTK main loop).  No locks needed.
    """

    __slots__ = (
        '_filepath',
        '_filename',
        '_is_dirty',
        '_is_imported',
        '_on_dirty_changed',
        '_suppress_callbacks',
        '_modified',
        '_created_at',
        '_modified_at',
    )

    def __init__(
        self,
        filename: str = "default",
        on_dirty_changed: Optional[Callable[[bool], None]] = None,
    ) -> None:
        self._filepath: Optional[str] = None
        self._filename: str = filename
        self._is_dirty: bool = False
        self._is_imported: bool = False
        self._on_dirty_changed: Optional[Callable[[bool], None]] = on_dirty_changed
        self._suppress_callbacks: bool = False
        now = datetime.now()
        self._modified: bool = False
        self._created_at: datetime = now
        self._modified_at: datetime = now

    # ------------------------------------------------------------------
    # Dirty state
    # ------------------------------------------------------------------

    def mark_dirty(self) -> None:
        """Mark document as having unsaved changes.

        Fires ``on_dirty_changed(True)`` on first transition.  Idempotent.
        Suppressed while ``suppress_callbacks`` is ``True``.
        """
        if not self._is_dirty:
            self._is_dirty = True
            if not self._suppress_callbacks and self._on_dirty_changed is not None:
                try:
                    self._on_dirty_changed(True)
                except Exception:
                    logger.debug("DocumentStateService.mark_dirty: callback failed", exc_info=True)

    def mark_clean(self) -> None:
        """Mark document as clean (all changes saved).

        Fires ``on_dirty_changed(False)`` on first transition.  Idempotent.
        """
        if self._is_dirty:
            self._is_dirty = False
            if not self._suppress_callbacks and self._on_dirty_changed is not None:
                try:
                    self._on_dirty_changed(False)
                except Exception:
                    logger.debug("DocumentStateService.mark_clean: callback failed", exc_info=True)

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty

    # ------------------------------------------------------------------
    # Modification timestamps / modified flag
    # ------------------------------------------------------------------

    def mark_modified(self) -> None:
        """Stamp modification time and implicitly mark dirty."""
        if not self._modified:
            self._modified = True
            self._modified_at = datetime.now()
            self.mark_dirty()

    def mark_as_saved(self) -> None:
        """Clear the imported flag after a successful save."""
        self._is_imported = False

    def mark_as_imported(self, imported_name: Optional[str] = None) -> None:
        """Flag the document as imported (triggers save-as on first save)."""
        self._is_imported = True
        if imported_name and imported_name != "default":
            self._filename = imported_name

    # ------------------------------------------------------------------
    # Filename / filepath
    # ------------------------------------------------------------------

    def set_filename(self, filename: str) -> None:
        """Set the base filename; marks document modified on change."""
        if filename != self._filename:
            self._filename = filename
            self.mark_modified()

    @property
    def filename(self) -> str:
        return self._filename

    @filename.setter
    def filename(self, value: str) -> None:
        self._filename = value

    def is_default_filename(self) -> bool:
        """``True`` for new/imported documents that have never been saved."""
        return self._filename == "default" or self._is_imported

    def set_filepath(self, filepath: str) -> None:
        """Set the full file path; also derives the base filename."""
        self._filepath = filepath
        if filepath:
            self._filename = os.path.splitext(os.path.basename(filepath))[0]
        else:
            self._filename = "default"

    @property
    def filepath(self) -> Optional[str]:
        return self._filepath

    @filepath.setter
    def filepath(self, value: Optional[str]) -> None:
        self._filepath = value

    def has_filepath(self) -> bool:
        return bool(self._filepath)

    def get_display_name(self) -> str:
        """Human-readable name: basename if saved, or base filename."""
        if self.has_filepath():
            return os.path.basename(self._filepath)  # type: ignore[arg-type]
        return "Untitled" if self._filename == "default" else self._filename

    # ------------------------------------------------------------------
    # Callback / suppression control
    # ------------------------------------------------------------------

    @property
    def on_dirty_changed(self) -> Optional[Callable[[bool], None]]:
        return self._on_dirty_changed

    @on_dirty_changed.setter
    def on_dirty_changed(self, callback: Optional[Callable[[bool], None]]) -> None:
        self._on_dirty_changed = callback

    @property
    def suppress_callbacks(self) -> bool:
        return self._suppress_callbacks

    @suppress_callbacks.setter
    def suppress_callbacks(self, value: bool) -> None:
        self._suppress_callbacks = value

    # ------------------------------------------------------------------
    # Extra accessors (not part of ABC but used by MCM internals)
    # ------------------------------------------------------------------

    @property
    def modified(self) -> bool:
        return self._modified

    @modified.setter
    def modified(self, value: bool) -> None:
        self._modified = value

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @created_at.setter
    def created_at(self, value: datetime) -> None:
        self._created_at = value

    @property
    def modified_at(self) -> datetime:
        return self._modified_at

    @modified_at.setter
    def modified_at(self, value: datetime) -> None:
        self._modified_at = value

    @property
    def is_imported(self) -> bool:
        return self._is_imported

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DocumentStateService("
            f"filename={self._filename!r}, filepath={self._filepath!r}, "
            f"dirty={self._is_dirty}, imported={self._is_imported})"
        )
