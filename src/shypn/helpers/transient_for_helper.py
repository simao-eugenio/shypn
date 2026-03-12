#!/usr/bin/env python3
"""
Wayland-safe transient dialog presentation helper.

Provides safe patterns for presenting transient dialogs under Wayland,
preventing Error 71 protocol errors through:

1. Automatic parent mapping validation
2. Delayed presentation when parent not ready
3. Fallback to non-transient presentation
4. Integration with WaylandParentManager

Usage:
    # Simple usage
    TransientForHelper.present_dialog(dialog, parent)
    
    # With document ID (recommended)
    parent_mgr = WaylandParentManager.get_instance()
    parent = parent_mgr.get_active_parent(document_id)
    TransientForHelper.present_dialog(dialog, parent)
    
    # Custom delay for state transitions
    TransientForHelper.present_dialog(dialog, parent, delay_ms=100)
"""

import logging
from typing import Optional
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

logger = logging.getLogger(__name__)


class TransientForHelper:
    """Helper for safe transient dialog presentation under Wayland.
    
    Handles all Wayland-specific timing and state validation to prevent
    protocol Error 71. Use this instead of directly calling:
        dialog.set_transient_for(parent)
        dialog.present()
    
    Benefits:
    - Automatic parent state validation
    - Delayed presentation when needed
    - Fallback handling
    - Comprehensive logging
    
    Thread-safety: Not thread-safe. Use from GTK main thread only.
    """
    
    @staticmethod
    def present_dialog(
        dialog: Gtk.Dialog,
        parent: Optional[Gtk.Window] = None,
        delay_ms: int = 50,
        max_retries: int = 3
    ) -> bool:
        """Present dialog with safe transient parent handling.
        
        Args:
            dialog: Dialog to present
            parent: Parent window (None for non-transient)
            delay_ms: Delay in milliseconds if parent not ready
            max_retries: Maximum retry attempts for delayed presentation
            
        Returns:
            True if dialog was presented immediately, False if delayed
        """
        # No parent = simple case
        if parent is None:
            logger.debug("[TransientForHelper] No parent, presenting dialog directly")
            dialog.present()
            return True
        
        # Check parent readiness
        parent_mapped = parent.get_mapped()
        parent_realized = parent.get_realized()
        
        logger.debug(
            f"[TransientForHelper] Parent state: mapped={parent_mapped}, "
            f"realized={parent_realized}"
        )
        
        if parent_mapped and parent_realized:
            # Safe to present immediately
            return TransientForHelper._present_immediate(dialog, parent)
        else:
            # Defer presentation
            logger.warning(
                f"[TransientForHelper] Parent not ready, deferring {delay_ms}ms "
                f"(mapped={parent_mapped}, realized={parent_realized})"
            )
            GLib.timeout_add(
                delay_ms,
                TransientForHelper._delayed_present,
                dialog,
                parent,
                delay_ms,
                max_retries
            )
            return False
    
    @staticmethod
    def present_dialog_safe(
        dialog: Gtk.Dialog,
        parent: Optional[Gtk.Window] = None,
        sync_compositor: bool = True
    ) -> bool:
        """Present dialog with comprehensive Wayland safety checks.
        
        Use this for dialogs presented during window state transitions
        (e.g., after maximize, fullscreen, tile operations).
        
        Args:
            dialog: Dialog to present
            parent: Parent window (None for non-transient)
            sync_compositor: Whether to sync compositor before presentation
            
        Returns:
            True if dialog was presented, False otherwise
        """
        if parent is None:
            dialog.present()
            return True
        
        # Check for problematic window states
        TransientForHelper._handle_window_state_transitions(parent)
        
        # Sync compositor if requested
        if sync_compositor:
            TransientForHelper._sync_compositor()
        
        # Now present
        return TransientForHelper.present_dialog(dialog, parent)
    
    @staticmethod
    def _present_immediate(dialog: Gtk.Dialog, parent: Gtk.Window) -> bool:
        """Present dialog immediately (parent is ready)."""
        try:
            dialog.set_transient_for(parent)
            dialog.present()
            logger.debug("[TransientForHelper] Dialog presented successfully")
            return True
        except (TypeError, AttributeError, RuntimeError) as e:
            logger.error(f"[TransientForHelper] Error presenting dialog: {e}", exc_info=True)
            # Fallback: present without transient parent
            dialog.present()
            return True
    
    @staticmethod
    def _delayed_present(
        dialog: Gtk.Dialog,
        parent: Gtk.Window,
        delay_ms: int,
        retries_left: int
    ) -> bool:
        """Delayed presentation callback (private)."""
        parent_mapped = parent.get_mapped()
        parent_realized = parent.get_realized()
        
        if parent_mapped and parent_realized:
            # Parent now ready, present
            logger.info("[TransientForHelper] Parent ready after delay, presenting")
            TransientForHelper._present_immediate(dialog, parent)
            return False  # Don't repeat timeout
        
        elif retries_left > 0:
            # Retry
            logger.warning(
                f"[TransientForHelper] Parent still not ready, retrying "
                f"({retries_left} retries left)"
            )
            GLib.timeout_add(
                delay_ms,
                TransientForHelper._delayed_present,
                dialog,
                parent,
                delay_ms,
                retries_left - 1
            )
            return False  # Don't repeat this timeout
        
        else:
            # Give up, present without transient parent
            logger.error(
                "[TransientForHelper] Parent never became ready, presenting "
                "without transient parent (may cause stacking issues)"
            )
            dialog.present()
            return False  # Don't repeat timeout
    
    @staticmethod
    def _handle_window_state_transitions(parent: Gtk.Window) -> None:
        """Check for problematic window states and delay if needed.
        
        When parent window is maximized, fullscreen, or tiled, the compositor
        may be in the middle of a state transition. Add small delay to let it settle.
        """
        window = parent.get_window()
        if not window:
            return
        
        state = window.get_state()
        is_maximized = bool(state & Gdk.WindowState.MAXIMIZED)
        is_fullscreen = bool(state & Gdk.WindowState.FULLSCREEN)
        is_tiled = bool(state & Gdk.WindowState.TILED)
        
        if is_maximized or is_fullscreen or is_tiled:
            logger.debug(
                f"[TransientForHelper] Special window state detected: "
                f"maximized={is_maximized}, fullscreen={is_fullscreen}, "
                f"tiled={is_tiled}, adding 100ms delay"
            )
            import time
            time.sleep(0.1)
    
    @staticmethod
    def _sync_compositor() -> None:
        """Wait for Wayland compositor to process pending events.
        
        Ensures compositor has processed all widget state changes before
        attempting to set transient parent.
        """
        display = Gdk.Display.get_default()
        if display:
            display.sync()
            logger.debug("[TransientForHelper] Compositor sync completed")
    
    @staticmethod
    def set_transient_safe(dialog: Gtk.Dialog, parent: Optional[Gtk.Window]) -> bool:
        """Set transient parent without presenting (advanced usage).
        
        Use this when you need to set transient parent but delay presentation
        (e.g., for custom presentation logic).
        
        Args:
            dialog: Dialog to set transient parent for
            parent: Parent window (None for no transient)
            
        Returns:
            True if transient was set, False otherwise
        """
        if parent is None:
            return False
        
        parent_mapped = parent.get_mapped()
        parent_realized = parent.get_realized()
        
        if not (parent_mapped and parent_realized):
            logger.warning(
                f"[TransientForHelper] set_transient_safe called with unready parent: "
                f"mapped={parent_mapped}, realized={parent_realized}"
            )
            return False
        
        try:
            dialog.set_transient_for(parent)
            logger.debug("[TransientForHelper] set_transient_for completed safely")
            return True
        except (TypeError, AttributeError, RuntimeError) as e:
            logger.error(f"[TransientForHelper] Error in set_transient_for: {e}", exc_info=True)
            return False
