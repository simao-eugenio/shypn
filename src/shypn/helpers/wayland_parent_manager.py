#!/usr/bin/env python3
"""
Wayland-safe parent window management for transient dialog presentation.

Provides centralized parent window tracking and validation to prevent
Wayland protocol Error 71 (xdg_toplevel buffer protocol errors).

Usage:
    # In MainWindow initialization
    parent_mgr = WaylandParentManager.get_instance()
    parent_mgr.register_parent(document_id, parent_window)
    
    # In panels/dialogs
    parent_mgr = WaylandParentManager.get_instance()
    parent = parent_mgr.get_active_parent(document_id)
    if parent:
        dialog.set_transient_for(parent)
        dialog.present()
"""

import logging
from typing import Dict, Optional
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

logger = logging.getLogger(__name__)


class WaylandParentManager:
    """Singleton manager for parent window references.
    
    Centralizes parent window tracking to ensure Wayland-safe
    transient dialog presentation. Prevents Error 71 by:
    
    1. Tracking window mapping state
    2. Monitoring realize/unrealize events
    3. Providing validation before set_transient_for()
    4. Logging warnings when parent not ready
    
    Thread-safety: Not thread-safe. Use from GTK main thread only.
    """
    
    _instance: Optional['WaylandParentManager'] = None
    
    def __init__(self):
        """Initialize parent manager (use get_instance() instead)."""
        self._active_parents: Dict[int, Gtk.Window] = {}  # document_id -> parent
        self._mapping_state: Dict[int, bool] = {}  # window_ptr -> is_mapped
        self._realize_state: Dict[int, bool] = {}  # window_ptr -> is_realized
        self._signal_handlers: Dict[int, tuple] = {}  # window_ptr -> (map_id, unmap_id, realize_id, unrealize_id)
        logger.info("[WaylandParentManager] Initialized")
    
    @classmethod
    def get_instance(cls) -> 'WaylandParentManager':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing only)."""
        if cls._instance:
            cls._instance._cleanup_all()
        cls._instance = None
    
    def register_parent(self, document_id: int, parent: Gtk.Window) -> None:
        """Register a parent window for a document.
        
        Args:
            document_id: Unique document identifier (typically id(drawing_area))
            parent: Parent window for transient dialogs
        """
        if document_id in self._active_parents:
            # Unregister old parent first
            self.unregister_parent(document_id)
        
        self._active_parents[document_id] = parent
        window_ptr = id(parent)
        
        # Track initial state
        self._mapping_state[window_ptr] = parent.get_mapped()
        self._realize_state[window_ptr] = parent.get_realized()
        
        # Connect state change signals
        map_id = parent.connect('map', self._on_parent_mapped, window_ptr)
        unmap_id = parent.connect('unmap', self._on_parent_unmapped, window_ptr)
        realize_id = parent.connect('realize', self._on_parent_realized, window_ptr)
        unrealize_id = parent.connect('unrealize', self._on_parent_unrealized, window_ptr)
        
        self._signal_handlers[window_ptr] = (map_id, unmap_id, realize_id, unrealize_id)
        
        logger.debug(
            f"[WaylandParentManager] Registered document {document_id}: "
            f"mapped={self._mapping_state[window_ptr]}, "
            f"realized={self._realize_state[window_ptr]}"
        )
    
    def unregister_parent(self, document_id: int) -> None:
        """Unregister a parent window (e.g., when document closes).
        
        Args:
            document_id: Document identifier to unregister
        """
        parent = self._active_parents.pop(document_id, None)
        if not parent:
            return
        
        window_ptr = id(parent)
        
        # Disconnect signals
        if window_ptr in self._signal_handlers:
            map_id, unmap_id, realize_id, unrealize_id = self._signal_handlers.pop(window_ptr)
            try:
                parent.disconnect(map_id)
                parent.disconnect(unmap_id)
                parent.disconnect(realize_id)
                parent.disconnect(unrealize_id)
            except (TypeError, AttributeError, RuntimeError) as e:
                logger.warning(f"[WaylandParentManager] Error disconnecting signals: {e}")
        
        # Clean up state
        self._mapping_state.pop(window_ptr, None)
        self._realize_state.pop(window_ptr, None)
        
        logger.debug(f"[WaylandParentManager] Unregistered document {document_id}")
    
    def get_active_parent(self, document_id: int) -> Optional[Gtk.Window]:
        """Get the active parent window for a document (Wayland-safe).
        
        Returns parent only if it's mapped and realized (safe for set_transient_for).
        
        Args:
            document_id: Document identifier
            
        Returns:
            Parent window if ready for set_transient_for(), None otherwise
        """
        parent = self._active_parents.get(document_id)
        if not parent:
            logger.debug(f"[WaylandParentManager] No parent registered for document {document_id}")
            return None
        
        window_ptr = id(parent)
        is_mapped = self._mapping_state.get(window_ptr, False)
        is_realized = self._realize_state.get(window_ptr, False)
        
        if is_mapped and is_realized:
            return parent
        else:
            logger.warning(
                f"[WaylandParentManager] Parent for document {document_id} not ready: "
                f"mapped={is_mapped}, realized={is_realized}"
            )
            return None
    
    def get_parent_unsafe(self, document_id: int) -> Optional[Gtk.Window]:
        """Get parent window without safety checks (use with caution).
        
        Use this only when you're handling state checking yourself
        (e.g., in TransientForHelper with delayed presentation).
        
        Args:
            document_id: Document identifier
            
        Returns:
            Parent window or None if not registered
        """
        return self._active_parents.get(document_id)
    
    def is_parent_ready(self, document_id: int) -> bool:
        """Check if parent is ready for set_transient_for().
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if parent is mapped and realized, False otherwise
        """
        parent = self._active_parents.get(document_id)
        if not parent:
            return False
        
        window_ptr = id(parent)
        is_mapped = self._mapping_state.get(window_ptr, False)
        is_realized = self._realize_state.get(window_ptr, False)
        
        return is_mapped and is_realized
    
    def get_all_document_ids(self) -> list:
        """Get all registered document IDs.
        
        Returns:
            List of document IDs with registered parents
        """
        return list(self._active_parents.keys())
    
    def _on_parent_mapped(self, parent: Gtk.Window, window_ptr: int) -> None:
        """Handle parent window map event."""
        self._mapping_state[window_ptr] = True
        logger.debug(f"[WaylandParentManager] Parent {window_ptr} mapped")
    
    def _on_parent_unmapped(self, parent: Gtk.Window, window_ptr: int) -> None:
        """Handle parent window unmap event."""
        self._mapping_state[window_ptr] = False
        logger.debug(f"[WaylandParentManager] Parent {window_ptr} unmapped")
    
    def _on_parent_realized(self, parent: Gtk.Window, window_ptr: int) -> None:
        """Handle parent window realize event."""
        self._realize_state[window_ptr] = True
        logger.debug(f"[WaylandParentManager] Parent {window_ptr} realized")
    
    def _on_parent_unrealized(self, parent: Gtk.Window, window_ptr: int) -> None:
        """Handle parent window unrealize event."""
        self._realize_state[window_ptr] = False
        logger.debug(f"[WaylandParentManager] Parent {window_ptr} unrealized")
    
    def _cleanup_all(self) -> None:
        """Clean up all tracked parents (for shutdown/testing)."""
        document_ids = list(self._active_parents.keys())
        for document_id in document_ids:
            self.unregister_parent(document_id)
        logger.info("[WaylandParentManager] Cleaned up all parents")
    
    def get_debug_info(self) -> Dict:
        """Get debug information about tracked parents.
        
        Returns:
            Dictionary with tracking state for debugging
        """
        info = {
            'active_parents': len(self._active_parents),
            'documents': {},
        }
        
        for doc_id, parent in self._active_parents.items():
            window_ptr = id(parent)
            info['documents'][doc_id] = {
                'window_ptr': window_ptr,
                'mapped': self._mapping_state.get(window_ptr, False),
                'realized': self._realize_state.get(window_ptr, False),
                'ready': self.is_parent_ready(doc_id),
            }
        
        return info
