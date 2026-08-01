"""Cruce de estimados entre la campana n (base) y la campana n+1."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Sequence

from .config import DEFAULT_CONFIG, MergeConfig
from .model import (
    Aporte,
    MergeReport,
    ceil_estimado,
    normalize_code,
    parse_estimado,
)


@dataclass
class MergeResult:
    """Salida del cruce, expresada como instrucciones sobre el archivo base."""

    #: indice 0-based de la fila de n -> estimado final (entero)
    estimados_base: dict[int, int]
    #: indices 0-based de filas de n+1 a copiar al final -> estimado final (entero)
    filas_nuevas: list[tuple[int, int]]
    report: MergeReport


def _index_base(
    filas_n: Sequence[Sequence[Any]], cfg: MergeConfig, report: MergeReport
) -> tuple[dict[tuple[str, str], int], dict[str, int]]:
    """Indexa n por (material, tipo) y por material, conservando la primera aparicion."""
    por_clave: dict[tuple[str, str], int] = {}
    por_material: dict[str, int] = {}
    vistas: dict[tuple[str, str], list[int]] = defaultdict(list)

    for i, fila in enumerate(filas_n):
        material = normalize_code(fila[cfg.col_material - 1])
        tipo = normalize_code(fila[cfg.col_tipo - 1])
        clave = (material, tipo)
        vistas[clave].append(i + cfg.first_data_row)
        por_clave.setdefault(clave, i)
        por_material.setdefault(material, i)

    report.claves_duplicadas_n = {k: v for k, v in vistas.items() if len(v) > 1}
    return por_clave, por_material


def merge_estimados(
    filas_n: Sequence[Sequence[Any]],
    filas_n1: Sequence[Sequence[Any]],
    cfg: MergeConfig = DEFAULT_CONFIG,
) -> MergeResult:
    """Aplica el cruce n / n+1 sobre la columna de estimado.

    Reglas (ver SPEC.md):
      * clave = material (B) + tipo (K).
      * clave en n y n+1  -> AO = AO_n + 5 % de AO_n+1.
      * material en n con otro tipo -> el 5 % se suma a la primera fila de ese material.
      * clave exclusiva de n+1 -> se copia la fila y AO queda solo con el 5 %.
      * el techo se aplica una sola vez, sobre el total acumulado.
    """
    report = MergeReport(filas_n=len(filas_n), filas_n1=len(filas_n1))
    por_clave, por_material = _index_base(filas_n, cfg, report)

    base_original = [parse_estimado(f[cfg.col_estimado - 1]) for f in filas_n]
    acumulado: dict[int, float] = defaultdict(float)
    nuevas: list[tuple[int, int]] = []
    vistas_n1: dict[tuple[str, str], list[int]] = defaultdict(list)

    for j, fila in enumerate(filas_n1):
        material = normalize_code(fila[cfg.col_material - 1])
        tipo = normalize_code(fila[cfg.col_tipo - 1])
        clave = (material, tipo)
        fila_excel = j + cfg.first_data_row
        vistas_n1[clave].append(fila_excel)

        aporte = parse_estimado(fila[cfg.col_estimado - 1]) * cfg.porcentaje

        destino = por_clave.get(clave)
        cruce = "exacta"
        if destino is None and cfg.fallback_por_material:
            destino = por_material.get(material)
            cruce = "material"

        if destino is None:
            nuevas.append((j, ceil_estimado(aporte)))
            report.filas_nuevas += 1
            continue

        acumulado[destino] += aporte
        registro = Aporte(
            material=material,
            tipo=tipo,
            estimado_n1=parse_estimado(fila[cfg.col_estimado - 1]),
            aporte=aporte,
            fila_n1=fila_excel,
            cruce=cruce,
        )
        report.aportes_por_fila.setdefault(destino, []).append(registro)
        if cruce == "exacta":
            report.cruces_exactos += 1
        else:
            report.cruces_por_material += 1
            report.cruces_cross_tipo.append(registro)

    report.claves_duplicadas_n1 = {k: v for k, v in vistas_n1.items() if len(v) > 1}

    estimados_base = {
        i: ceil_estimado(base_original[i] + acumulado.get(i, 0.0))
        for i in range(len(filas_n))
    }
    report.filas_resultado = len(filas_n) + len(nuevas)

    return MergeResult(estimados_base=estimados_base, filas_nuevas=nuevas, report=report)
