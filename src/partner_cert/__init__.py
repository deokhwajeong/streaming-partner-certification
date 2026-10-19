"""Certification gate engine for streaming partner apps on a TV platform."""

from .engine import Evaluation, evaluate, evaluate_cell
from .loader import DataError, Dataset, load_dataset
from .model import Decision, Recommendation, Severity, Status

__version__ = "0.1.0"

__all__ = [
    "DataError",
    "Dataset",
    "Decision",
    "Evaluation",
    "Recommendation",
    "Severity",
    "Status",
    "evaluate",
    "evaluate_cell",
    "load_dataset",
]
