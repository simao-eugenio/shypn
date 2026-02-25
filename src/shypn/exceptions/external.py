"""External API exceptions (KEGG and similar services)."""

from shypn.exceptions.base import ShypnError


class KEGGError(ShypnError):
    """Errors related to KEGG API or data.

    Base class for KEGG-related errors.
    """
    pass


class KEGGConnectionError(KEGGError):
    """Cannot connect to KEGG API.

    Raised when:
    - Network connection fails
    - KEGG API is unavailable
    - Request times out
    """
    pass


class KEGGDataError(KEGGError):
    """Invalid or unexpected KEGG data.

    Raised when:
    - KEGG response is malformed
    - Expected data is missing
    - Data format is unexpected
    """
    pass
