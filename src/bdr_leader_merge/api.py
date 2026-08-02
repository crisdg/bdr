"""Punto de entrada unico de la consolidacion, compartido por la CLI y la GUI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import DEFAULT_CONFIG, MergeConfig
from .excel_io import read_rows, write_merged
from .merge import MergeResult, merge_estimados


@dataclass
class ConsolidationOutcome:
    path: Path
    result: MergeResult


def consolidate(
    path_n: Path,
    path_n1: Path,
    path_out: Path,
    cfg: MergeConfig = DEFAULT_CONFIG,
) -> ConsolidationOutcome:
    """Cruza n con el 5 % de n+1 y escribe el resultado en path_out."""
    filas_n = read_rows(path_n, cfg)
    filas_n1 = read_rows(path_n1, cfg)
    result = merge_estimados(filas_n, filas_n1, cfg)
    escrito = write_merged(path_n, path_n1, path_out, result, cfg)
    return ConsolidationOutcome(path=escrito, result=result)
