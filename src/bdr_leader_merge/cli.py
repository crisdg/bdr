"""Interfaz de linea de comandos del cruce LEADER n / n+1."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compare import compare_files
from .config import DEFAULT_CONFIG
from .excel_io import read_rows, write_merged
from .merge import merge_estimados

MAX_EJEMPLOS = 10


def _print_report(result, max_ejemplos: int = MAX_EJEMPLOS) -> None:
    rep = result.report
    print(rep.resumen())

    if rep.claves_duplicadas_n:
        print(f"\nClaves (material,tipo) duplicadas en n -> el aporte va a la primera fila:")
        for (mat, tipo), filas in list(rep.claves_duplicadas_n.items())[:max_ejemplos]:
            print(f"  material {mat} tipo {tipo}: filas {filas}")

    if rep.cruces_cross_tipo:
        print(f"\nCruces por material con tipo distinto ({len(rep.cruces_cross_tipo)}):")
        for ap in rep.cruces_cross_tipo[:max_ejemplos]:
            print(
                f"  material {ap.material} tipo n+1 {ap.tipo} "
                f"(fila n+1 {ap.fila_n1}) aporta {ap.aporte:g}"
            )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bdr-leader-merge",
        description="Cruza el estimado (AO) de la campana n con el 5 % de la campana n+1.",
    )
    p.add_argument("--n", required=True, type=Path, help="Archivo LEADER campana n (base)")
    p.add_argument("--n1", required=True, type=Path, help="Archivo LEADER campana n+1")
    p.add_argument("--out", required=True, type=Path, help="Archivo de salida")
    p.add_argument(
        "--reference",
        type=Path,
        help="Archivo de referencia para validar el resultado (opcional)",
    )
    p.add_argument(
        "--max-ejemplos",
        type=int,
        default=MAX_EJEMPLOS,
        help="Cantidad maxima de ejemplos por seccion del reporte (default: 10)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = DEFAULT_CONFIG

    for etiqueta, ruta in (("n", args.n), ("n+1", args.n1)):
        if not ruta.exists():
            print(f"error: no existe el archivo {etiqueta}: {ruta}", file=sys.stderr)
            return 2

    filas_n = read_rows(args.n, cfg)
    filas_n1 = read_rows(args.n1, cfg)
    result = merge_estimados(filas_n, filas_n1, cfg)
    _print_report(result, args.max_ejemplos)

    write_merged(args.n, args.n1, args.out, result, cfg)
    print(f"\nresultado escrito en: {args.out}")

    if args.reference:
        if not args.reference.exists():
            print(f"error: no existe la referencia: {args.reference}", file=sys.stderr)
            return 2
        rep = compare_files(args.out, args.reference, cfg)
        print("\n--- validacion contra referencia ---")
        print(rep.resumen())
        for d in rep.diferencias_estimado[: args.max_ejemplos]:
            print(
                f"  AO fila {d.fila_excel} material {d.material} tipo {d.tipo}: "
                f"calculado={d.calculado:g} referencia={d.referencia:g}"
            )
        for d in rep.diferencias_otras[: args.max_ejemplos]:
            print(
                f"  {d.columna} fila {d.fila_excel}: "
                f"calculado={d.calculado!r} referencia={d.referencia!r}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
