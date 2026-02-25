"""Import / export and file-I/O exceptions."""

from shypn.exceptions.base import ShypnError


class ImportExportError(ShypnError):
    """Errors during import or export operations.

    Base class for all file I/O related errors.
    """
    pass


class FileFormatError(ImportExportError):
    """Unsupported or invalid file format.

    Raised when:
    - File format is not recognized
    - File structure is invalid
    - Required file elements are missing
    """
    pass


class ParseError(ImportExportError):
    """Error parsing file content.

    Raised when file content cannot be parsed correctly.
    """
    pass


class ExportError(ImportExportError):
    """Error exporting model or data.

    Raised when export operation fails.
    """
    pass
