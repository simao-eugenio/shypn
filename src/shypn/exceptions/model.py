"""Model-structure and validation exceptions."""

from shypn.exceptions.base import ShypnError


class ModelError(ShypnError):
    """Errors related to model structure or validation.

    Raised when:
    - Model structure is invalid (missing required elements)
    - Model validation fails
    - Model constraints are violated
    - Inconsistent model state
    """
    pass
