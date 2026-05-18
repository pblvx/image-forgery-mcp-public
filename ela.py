class ForensicError(Exception):
    """Base exception for all forensic errors."""
    pass

class UnsupportedFormatError(ForensicError):
    """Raised when the image format is not supported."""
    pass

class AnalysisError(ForensicError):
    """Raised when an error occurs during the analysis process."""
    pass
