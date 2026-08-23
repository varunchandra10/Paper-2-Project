class PaperToProjectException(Exception):
    """Base exception for all Paper-to-Project backend pipeline failures."""
    pass


class ExtractionException(PaperToProjectException):
    """Exception raised when document parser or layout extraction fails."""
    pass


class FeasibilityException(PaperToProjectException):
    """Exception raised when project constraints render implementation impossible."""
    pass


class APIException(PaperToProjectException):
    """Exception raised during server endpoints or SSE stream failures."""
    pass
