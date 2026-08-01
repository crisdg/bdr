# bdr

App para proceso de datos para BDR.

## bdr-leader-merge

Cruza el estimado (`Unidades estimadas x Pedido`, columna `AO`) de una planilla LEADER de
la campana `n` con el 5 % del estimado de la campana `n+1`, usando **material (`B`) +
tipo (`K`)** como clave y dejando el resto de la planilla intacto.

Las reglas completas y validadas estan en [`SPEC.md`](SPEC.md).

### Instalacion

```bash
python -m pip install -r requirements.txt
```

O como paquete instalable:

```bash
python -m pip install -e .
```

### Uso

```bash
python -m bdr_leader_merge.cli \
  --n  "LEADER C12 2026.XLSX" \
  --n1 "LEADER C13 2026.XLSX" \
  --out "salida/LEADER C12 2026 con cod c13 - generado.xlsx"
```

Con el paquete instalado tambien esta disponible el comando `bdr-leader-merge`.

Si se define `--reference`, el resultado se compara celda por celda contra un archivo ya
validado y se listan las diferencias:

```bash
python -m bdr_leader_merge.cli \
  --n  "LEADER C12 2026.XLSX" \
  --n1 "LEADER C13 2026.XLSX" \
  --out "salida/generado.xlsx" \
  --reference "LEADER C12 2026 con cod c13.xlsx"
```

Opciones:

| Opcion | Descripcion |
| --- | --- |
| `--n` | Archivo de la campana `n` (base). Obligatorio. |
| `--n1` | Archivo de la campana `n+1`. Obligatorio. |
| `--out` | Archivo de salida. Obligatorio. |
| `--reference` | Archivo de referencia para validar el resultado. |
| `--max-ejemplos` | Ejemplos por seccion del reporte (default: 10). |

### Reporte

El proceso informa filas de entrada y salida, cruces por material+tipo, cruces resueltos
solo por material, filas nuevas, y las claves duplicadas detectadas en la campana `n`.

Resultado del caso C12 -> C13:

```
filas n (base)            : 877
filas n+1                 : 831
filas resultado           : 1467
cruces material+tipo      : 229
cruces solo material      : 12
filas nuevas desde n+1    : 590
claves duplicadas en n    : 1

estimado (AO) coincidente: 1465/1467
diferencias en otras columnas: 0
```

Las 2 diferencias restantes son correcciones manuales del archivo de referencia,
detalladas en la seccion 7 de [`SPEC.md`](SPEC.md).

### Estructura

```
src/bdr_leader_merge/
  config.py     parametros: columnas, porcentaje, epsilon del techo
  model.py      normalizacion de claves/estimados y estructuras del reporte
  merge.py      logica del cruce (independiente de Excel)
  excel_io.py   lectura y escritura preservando el archivo base
  compare.py    validacion contra un archivo de referencia
  cli.py        interfaz de linea de comandos
tests/          pruebas con planillas sinteticas
```

### Tests

```bash
python -m pytest
```
