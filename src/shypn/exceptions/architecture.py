"""Architecture-level exceptions (use carefully)."""

from shypn.exceptions.base import ShypnError


class DocumentError(ShypnError):
    """Errors in document lifecycle management.

    ⚠️ WARNING: Use this exception carefully!

    This should ONLY be used for document-specific errors in the
    Multi-Document Architecture. Most errors should use more specific
    exception types (ModelError, SimulationError, etc.)

    Raised when:
    - Document cannot be created
    - Document state is invalid
    - Document cleanup fails
    """
    pass


class EventBusError(ShypnError):
    """Errors in EventBus operation.

    ⚠️ WARNING: This should be EXTREMELY RARE!

    The EventBus is part of the protected A+ architecture and should
    be highly reliable. If you're seeing this error, there may be a
    fundamental architecture issue.

    Raised when:
    - Event dispatch fails unexpectedly
    - Subscriber registration fails
    - Event bus state is corrupted
    """
    pass
