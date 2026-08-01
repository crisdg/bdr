"""Comparacion del resultado calculado contra un archivo de referencia."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import openpyxl

from .config import DEFAULT_CONFIG, MergeConfig
from .model import normalize_code, parse_estimado


@dataclass
class Diferencia:
    fila_excel: int
    columna: str
    material: str
    tipo: str
    calculado: Any
    referencia: Any


@dataclass
class CompareReport:
    filas_calculadas: int = 0
    filas_referencia: int = 0
    celdas_estimado_iguales: int = 0
    diferencias_estimado: list[Diferencia] = field(default_factory=list)
    diferencias_otras: list[Diferencia] = field(default_factory=list)

    def resumen(self) -> str:
        total = self.celdas_estimado_iguales + len(self.diferencias_estimado)
        return (
            f"filas: calculado={self.filas_calculadas} referencia={self.filas_referencia}\n"
            f"estimado (AO) coincidente: {self.celdas_estimado_iguales}/{total}\n"
            f"diferencias en AO: {len(self.diferencias_estimado)}\n"
            f"diferencias en otras columnas: {len(self.diferencias_otras)}"
        )


def _equal(a: Any, b: Any) -> bool:
    sa = "" if a is None else str(a).strip()
    sb = "" if b is None else str(b).strip()
    if sa == sb:
        return True
    try:
        return abs(float(sa or 0) - float(sb or 0)) < 1e-9
    except ValueError:
        return False


def compare_files(
    path_calculado: Path,
    path_referencia: Path,
    cfg: MergeConfig = DEFAULT_CONFIG,
) -> CompareReport:
    from .excel_io import read_rows

    calc = read_rows(path_calculado, cfg)
    ref = read_rows(path_referencia, cfg)
    rep = CompareReport(filas_calculadas=len(calc), filas_referencia=len(ref))

    for i in range(min(len(calc), len(ref))):
        fila_c, fila_r = calc[i], ref[i]
        material = normalize_code(fila_c[cfg.col_material - 1])
        tipo = normalize_code(fila_c[cfg.col_tipo - 1])
        fila_excel = i + cfg.first_data_row

        got = parse_estimado(fila_c[cfg.col_estimado - 1])
        want = parse_estimado(fila_r[cfg.col_estimado - 1])
        if abs(got - want) < 1e-6:
            rep.celdas_estimado_iguales += 1
        else:
            rep.diferencias_estimado.append(
                Diferencia(fila_excel, "AO", material, tipo, got, want)
            )

        for col in range(1, min(len(fila_c), len(fila_r)) + 1):
            if col == cfg.col_estimado:
                continue
            if not _equal(fila_c[col - 1], fila_r[col - 1]):
                rep.diferencias_otras.append(
                    Diferencia(
                        fila_excel,
                        openpyxl.utils.get_column_letter(col),
                        material,
                        tipo,
                        fila_c[col - 1],
                        fila_r[col - 1],
                    )
                )

    return rep
