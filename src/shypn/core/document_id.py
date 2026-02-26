"""Stable per-document integer identifiers for EventBus routing.

Problem solved:
    Using id(widget) as a document identifier is unsafe: Python may reuse the
    memory address of a destroyed GtkDrawingArea for a new widget. Two
    documents then share the same identifier, causing EventBus to route events
    from the new document to any subscribers that were registered for the old
    document but were not cleaned up before the address was reused.

Solution:
    Assign a monotonically incrementing integer to each document at creation
    time (``drawing._shypn_doc_id = alloc_doc_id()``).  Use ``doc_id(widget)``
    wherever an EventBus ``document_id=`` argument is required.

    The counter never wraps (Python int is unbounded) and never repeats within
    a process lifetime, so address reuse is impossible.

Backward compatibility:
    ``doc_id(widget)`` falls back to ``id(widget)`` when ``_shypn_doc_id`` has
    not been assigned (e.g. widgets created before this module was introduced).
    This makes the change non-breaking for any code path that hasn't been
    updated yet.

Usage::

    # In model_canvas_loader.add_document() — assign once per new tab
    from shypn.core.document_id import alloc_doc_id
    drawing._shypn_doc_id = alloc_doc_id()

    # Everywhere else — read the stable ID
    from shypn.core.document_id import doc_id
    EventBus.emit('model.changed', data, document_id=doc_id(drawing_area))
    EventBus.clear_document(doc_id(drawing_area))
"""

import itertools

_counter = itertools.count(1)


def alloc_doc_id() -> int:
    """Allocate a new unique document ID.

    Returns:
        int: A positive integer that is unique within this process lifetime.
             Never reused, never zero.
    """
    return next(_counter)


def doc_id(widget) -> int:
    """Return the stable document ID for a GTK widget.

    If the widget has a ``_shypn_doc_id`` attribute (set by
    :func:`alloc_doc_id`), that value is returned.  Otherwise falls back to
    ``id(widget)`` for backward compatibility with code paths not yet updated.

    Args:
        widget: Any object, typically a GtkDrawingArea.

    Returns:
        int: The document ID to use as the ``document_id=`` argument in
             EventBus calls.
    """
    return getattr(widget, '_shypn_doc_id', id(widget))
