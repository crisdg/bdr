"""Normalizacion de claves y valores de las planillas LEADER."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .config import CEIL_EPSILON


def normalize_code(value: Any) -> str:
    """Normaliza material y tipo.

    Los exports llegan como texto con ceros a la izquierda ('000015', '09') o como
    numero segun la celda, asi que se comparan sin ceros iniciales ni sufijo '.0'.
    """
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if text.endswith(".0") and text[:-2].lstrip("-").isdigit():
        text = text[:-2]
    stripped = text.lstrip("0")
    return stripped if stripped else "0"


def parse_estimado(value: Any) -> float:
    """Lee AO, que puede venir como texto rellenado con ceros ('000020')."""
    if value is None:
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"Estimado no numerico en AO: {value!r}") from exc


def ceil_estimado(value: float) -> int:
    """Techo del estimado; toda fraccion escala a la unidad siguiente."""
    return math.ceil(value - CEIL_EPSILON)


def is_blank_row(values: list[Any]) -> bool:
    return all(v is None or str(v).strip() == "" for v in values)


@dataclass
class Aporte:
    """Contribucion de una fila de n+1 sobre una fila de n."""

    material: str
    tipo: str
    estimado_n1: float
    aporte: float
    fila_n1: int
    cruce: str  # "exacta" | "material"


@dataclass
class MergeReport:
    filas_n: int = 0
    filas_n1: int = 0
    filas_resultado: int = 0
    cruces_exactos: int = 0
    cruces_por_material: int = 0
    filas_nuevas: int = 0
    claves_duplicadas_n: dict[tuple[str, str], list[int]] = field(default_factory=dict)
    claves_duplicadas_n1: dict[tuple[str, str], list[int]] = field(default_factory=dict)
    aportes_por_fila: dict[int, list[Aporte]] = field(default_factory=dict)
    cruces_cross_tipo: list[Aporte] = field(default_factory=list)

    @property
    def filas_afectadas(self) -> int:
        return len(self.aportes_por_fila)

    def resumen(self) -> str:
        lineas = [
            f"filas n (base)            : {self.filas_n}",
            f"filas n+1                 : {self.filas_n1}",
            f"filas resultado           : {self.filas_resultado}",
            f"cruces material+tipo      : {self.cruces_exactos}",
            f"cruces solo material      : {self.cruces_por_material}",
            f"filas nuevas desde n+1    : {self.filas_nuevas}",
            f"filas de n con aporte     : {self.filas_afectadas}",
            f"claves duplicadas en n    : {len(self.claves_duplicadas_n)}",
            f"claves duplicadas en n+1  : {len(self.claves_duplicadas_n1)}",
        ]
        return "\n".join(lineas)
