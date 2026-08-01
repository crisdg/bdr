"""Constructores de planillas sinteticas con el layout LEADER (A..AW)."""

from pathlib import Path

import openpyxl

from bdr_leader_merge.config import DEFAULT_CONFIG

CFG = DEFAULT_CONFIG
N_COLS = 49


def make_row(material, tipo, estimado, marca="X"):
    """Fila completa A..AW con material (B), tipo (K) y estimado (AO)."""
    fila = [None] * N_COLS
    fila[0] = "Verdadero, si, 1 ..."
    fila[CFG.col_material - 1] = material
    fila[2] = "Auxiliares de Ventas"
    fila[8] = f"DESC {material}"
    fila[CFG.col_tipo - 1] = tipo
    fila[CFG.col_estimado - 1] = estimado
    fila[N_COLS - 1] = marca
    return fila


def write_workbook(path: Path, filas):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append([f"H{i}" for i in range(1, N_COLS + 1)])
    for fila in filas:
        ws.append(fila)
    wb.save(path)
    wb.close()
    return path
