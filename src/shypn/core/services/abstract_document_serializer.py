"""AbstractDocumentSerializer — ABC for document serialization/deserialization.

Sprint 20 — Phase 7: defines the typed contract for document serialization
operations extracted from ``ModelCanvasManager``.

Concrete implementation:
    :class:`~shypn.core.services.document_serializer.DocumentSerializer`
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass  # MCM forward-ref avoided to prevent circular imports

__all__ = ["AbstractDocumentSerializer"]


class AbstractDocumentSerializer(ABC):
    """Typed contract for round-tripping a document to/from its on-disk form.

    All methods receive the canvas manager as a parameter (stateless service
    pattern) so that the serializer can be instantiated once and re-used for
    many documents.  This also makes it straightforward to inject a test
    double.
    """

    # ------------------------------------------------------------------
    # Primary serialization
    # ------------------------------------------------------------------

    @abstractmethod
    def to_document_model(self, manager: Any) -> Any:
        """Convert *manager*'s Petri net objects to a ``DocumentModel``.

        Must temporarily reset analysis colours before building the model
        and restore them afterwards so that the live canvas is unaffected.

        Returns
        -------
        DocumentModel
            A fully-populated model ready for persistence.
        """

    # ------------------------------------------------------------------
    # View-state persistence
    # ------------------------------------------------------------------

    @abstractmethod
    def get_view_state(self, manager: Any) -> Dict[str, Any]:
        """Return a JSON-serialisable dict of the current view state."""

    @abstractmethod
    def set_view_state(self, manager: Any, view_state: Optional[Dict[str, Any]]) -> None:
        """Restore view state (zoom, pan, rotation) from *view_state*."""

    @abstractmethod
    def save_view_state_to_file(
        self, manager: Any, filepath: Optional[str] = None
    ) -> bool:
        """Persist the current view state to a JSON side-car file.

        Returns ``True`` on success, ``False`` on any I/O failure.
        """

    @abstractmethod
    def load_view_state_from_file(
        self, manager: Any, filepath: Optional[str] = None
    ) -> bool:
        """Restore view state from the JSON side-car file.

        Falls back to :meth:`center_view_on_content` when the file does not
        exist.  Returns ``True`` on success, ``False`` otherwise.
        """

    # ------------------------------------------------------------------
    # Document metadata snapshot
    # ------------------------------------------------------------------

    @abstractmethod
    def get_document_state(self, manager: Any) -> Dict[str, Any]:
        """Return a snapshot dict of metadata about the current document."""
