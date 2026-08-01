"""Parametros del cruce LEADER campana n / n+1."""

from __future__ import annotations

from dataclasses import dataclass

COL_MATERIAL = 2   # B - Material
COL_TIPO = 11      # K - Tipo Material
COL_ESTIMADO = 41  # AO - Unidades estimadas x Pedido

HEADER_ROW = 1
FIRST_DATA_ROW = 2
TOTAL_COLUMNS = 49  # A..AW

PORCENTAJE_N1 = 0.05

# Tolerancia para absorber el error binario de floats antes de aplicar el techo:
# sin esto, 135.00000000000003 escalaria a 136.
CEIL_EPSILON = 1e-9


@dataclass(frozen=True)
class MergeConfig:
    col_material: int = COL_MATERIAL
    col_tipo: int = COL_TIPO
    col_estimado: int = COL_ESTIMADO
    first_data_row: int = FIRST_DATA_ROW
    porcentaje: float = PORCENTAJE_N1
    #: Si el material existe en n pero con otro tipo, sumar a su primera aparicion.
    fallback_por_material: bool = True


DEFAULT_CONFIG = MergeConfig()
