"""Cruce de estimados LEADER entre campanas consecutivas (n y n+1)."""

from .api import ConsolidationOutcome, consolidate
from .compare import CompareReport, compare_files
from .config import DEFAULT_CONFIG, MergeConfig
from .excel_io import read_rows, write_merged
from .merge import MergeResult, merge_estimados
from .model import MergeReport, ceil_estimado, normalize_code, parse_estimado

__version__ = "0.1.0"

__all__ = [
    "ConsolidationOutcome",
    "consolidate",
    "CompareReport",
    "compare_files",
    "DEFAULT_CONFIG",
    "MergeConfig",
    "read_rows",
    "write_merged",
    "MergeResult",
    "merge_estimados",
    "MergeReport",
    "ceil_estimado",
    "normalize_code",
    "parse_estimado",
]
