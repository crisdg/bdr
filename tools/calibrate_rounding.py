"""Verifica que la regla de redondeo de SPEC.md siga siendo la que mejor reproduce
un archivo de referencia.

Util cuando aparece un par de campanas nuevo y se quiere confirmar que el criterio
(techo sobre el total acumulado, sin redondeo parcial) sigue vigente.

    python tools/calibrate_rounding.py --n C12.xlsx --n1 C13.xlsx --ref REF.xlsx
"""

from __future__ import annotations

import argparse
import math
import sys
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bdr_leader_merge.config import DEFAULT_CONFIG  # noqa: E402
from bdr_leader_merge.excel_io import read_rows  # noqa: E402
from bdr_leader_merge.model import normalize_code, parse_estimado  # noqa: E402

CFG = DEFAULT_CONFIG

REDONDEOS = {
    "ceil": lambda x: math.ceil(x - 1e-9),
    "floor": lambda x: math.floor(x + 1e-9),
    "half_up": lambda x: int(Decimal(repr(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
    "round": lambda x: int(round(x)),
}


def estimados_resultado(filas_n, filas_n1, redondeo_parcial, redondeo_total):
    por_clave, por_material = {}, {}
    for i, f in enumerate(filas_n):
        mat = normalize_code(f[CFG.col_material - 1])
        tipo = normalize_code(f[CFG.col_tipo - 1])
        por_clave.setdefault((mat, tipo), i)
        por_material.setdefault(mat, i)

    base = [parse_estimado(f[CFG.col_estimado - 1]) for f in filas_n]
    acum = defaultdict(float)
    nuevas = []
    for f in filas_n1:
        mat = normalize_code(f[CFG.col_material - 1])
        tipo = normalize_code(f[CFG.col_tipo - 1])
        aporte = parse_estimado(f[CFG.col_estimado - 1]) * CFG.porcentaje
        destino = por_clave.get((mat, tipo), por_material.get(mat))
        if destino is None:
            nuevas.append(aporte)
        else:
            acum[destino] += redondeo_parcial(aporte) if redondeo_parcial else aporte

    salida = [redondeo_total(base[i] + acum.get(i, 0.0)) for i in range(len(filas_n))]
    salida.extend(redondeo_total(a) for a in nuevas)
    return salida


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", required=True, type=Path)
    p.add_argument("--n1", required=True, type=Path)
    p.add_argument("--ref", required=True, type=Path)
    args = p.parse_args()

    filas_n = read_rows(args.n)
    filas_n1 = read_rows(args.n1)
    filas_ref = read_rows(args.ref)
    ref = [parse_estimado(f[CFG.col_estimado - 1]) for f in filas_ref]

    print(f"{'estrategia':<38} {'iguales':>8} {'difs':>6}")
    resultados = []
    for nombre_total, fn_total in REDONDEOS.items():
        for nombre_parcial, fn_parcial in [("sin_redondeo_parcial", None), *REDONDEOS.items()]:
            calc = estimados_resultado(filas_n, filas_n1, fn_parcial, fn_total)
            if len(calc) != len(ref):
                print(f"  longitud distinta: {len(calc)} vs {len(ref)}")
                continue
            difs = sum(1 for a, b in zip(calc, ref) if abs(a - b) > 1e-6)
            etiqueta = f"total={nombre_total}, 5%={nombre_parcial}"
            print(f"{etiqueta:<38} {len(calc) - difs:>8} {difs:>6}")
            resultados.append((difs, etiqueta))

    if resultados:
        difs, etiqueta = min(resultados)
        print(f"\nmejor: {etiqueta} -> {difs} diferencias")
        esperado = "total=ceil, 5%=sin_redondeo_parcial"
        estado = "coincide con SPEC.md" if etiqueta == esperado else f"NO coincide con SPEC.md ({esperado})"
        print(estado)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
