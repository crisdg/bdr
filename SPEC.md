# SPEC — bdr-leader-merge

Reglas confirmadas del cruce de estimados entre la campana `n` (archivo base) y la
campana `n+1`. Validadas contra `LEADER C12 2026 con cod c13.xlsx`: **1465 / 1467 celdas
de AO coinciden y las 48 columnas restantes coinciden al 100 %**. Las 2 diferencias son
correcciones manuales de la referencia y estan documentadas al final.

## 1. Archivos

| Rol | Archivo del caso C12/C13 |
| --- | --- |
| Campana `n` (base) | `LEADER C12 2026.XLSX` |
| Campana `n+1` | `LEADER C13 2026.XLSX` |
| Referencia de validacion | `LEADER C12 2026 con cod c13.xlsx` |

Los tres comparten el mismo layout: una hoja, encabezado en la fila 1, datos desde la
fila 2, columnas `A`..`AW` (49 columnas).

## 2. Mapeo de columnas

| Columna | Indice | Encabezado | Rol |
| --- | --- | --- | --- |
| `B` | 2 | `Material` | material (clave) |
| `K` | 11 | `Tipo Material` | tipo (clave) |
| `AO` | 41 | `Unidades estimadas x Pedido` | estimado (unico valor que se modifica) |

> El enunciado original decia "la columna de material es K". Es un error de tipeo
> verificado contra los archivos: `K` es **solo** el tipo y el material vive en `B`.

### Normalizacion

- Material y tipo se exportan como texto con ceros a la izquierda (`'000015'`, `'09'`)
  y a veces como numero. Se comparan sin ceros iniciales ni sufijo `.0`, de modo que
  `'000015'`, `15`, `15.0` y `'15'` son la misma clave; idem `'09'` y `9`.
- `AO` tambien llega como texto rellenado (`'000020'`). Se lee como numero y se
  **escribe como entero numerico**, igual que en la referencia.

## 3. Regla de cruce

Clave = **material + tipo**. Para cada fila de `n+1`, en este orden de prioridad:

1. **Coincidencia exacta** (mismo material y mismo tipo en `n`): el 5 % del estimado de
   `n+1` se suma al estimado de esa fila de `n`.
2. **Coincidencia solo por material** (el material existe en `n` pero con otro tipo): el
   5 % se suma a la **primera aparicion** de ese material en `n`, aunque el tipo difiera.
3. **Sin coincidencia**: la fila de `n+1` se copia completa al final del resultado y en
   `AO` queda **unicamente** el 5 %.

Formalmente, para una fila de `n` en la posicion `i`:

```
AO_resultado(i) = ceil( AO_n(i) + sum( 0.05 * AO_n+1(j) para cada j asignado a i ) )
```

y para una fila exclusiva de `n+1`:

```
AO_resultado = ceil( 0.05 * AO_n+1 )
```

### Redondeo

- Se aplica **techo (`ceil`)**, no redondeo al mas cercano: cualquier fraccion escala al
  entero siguiente. Ejemplo real: `9 + 0.45 = 9.45 -> 10`.
- El techo se aplica **una sola vez, sobre el total acumulado**, nunca a cada aporte por
  separado. Ejemplo: `10 + 125 + 0.5 = 135.5 -> 136` (no `10 + 125 + 1`).
- Se descuenta un epsilon de `1e-9` antes del techo para que el error binario de los
  floats no infle el resultado (`135.00000000000003` debe dar `135`, no `136`).

Esta combinacion se determino empiricamente probando 20 variantes (`ceil` / `floor` /
`half_up` / `round` aplicados al total y/o a cada aporte) contra la referencia: `ceil`
sobre el total sin redondeo parcial es la unica que llega a 1465/1467; la siguiente
mejor deja 3 diferencias y el resto entre 99 y 612.

## 4. Preservacion del resto de la planilla

- **Las otras 48 columnas no se tocan.** El resultado se construye abriendo el archivo
  base y sobrescribiendo unicamente celdas de `AO`, con lo que se conservan valores,
  formatos y estilos originales.
- El orden de las filas de `n` se mantiene; las filas nuevas se agregan al final en el
  orden en que aparecen en `n+1`.
- Las filas nuevas se copian celda por celda desde `n+1` (valor, formato numerico y
  alineacion), salvo `AO`.
- Las filas de `n` sin contraparte en `n+1` conservan su estimado original (solo pasa de
  texto rellenado a entero).

## 5. Duplicados

- **`n` (C12):** 877 filas, 720 materiales, 876 claves `(material, tipo)`. Hay **una**
  clave duplicada: material `500778` tipo `4` en las filas 627 y 628. Ademas 154
  materiales aparecen en mas de una fila con tipos distintos, que es lo normal
  (por ejemplo tipos `09` y `14` del mismo material).
- **`n+1` (C13):** 831 filas, 817 materiales, 831 claves — **sin duplicados**.
- **Criterio ante clave duplicada en `n`:** el aporte se suma a la **primera** fila; las
  repeticiones posteriores no reciben nada. Se reportan en la salida para revision.

## 6. Conteos del cruce C12 -> C13

| Concepto | Cantidad |
| --- | --- |
| Filas de datos en `n` | 877 |
| Filas de datos en `n+1` | 831 |
| Cruces por material + tipo | 229 |
| Cruces solo por material (tipo distinto) | 12 |
| Filas exclusivas de `n+1` (nuevas) | 590 |
| Filas de `n` que reciben algun aporte | 237 |
| **Filas del resultado** | **1467** = 877 + 590 |

El total de 1467 coincide exactamente con la referencia.

## 7. Diferencias contra la referencia (correcciones manuales)

Las 2 unicas discrepancias caen justamente en los dos escenarios ambiguos: la clave
duplicada y un cruce por tipo distinto.

| Fila | Material / tipo | Calculado | Referencia | Explicacion |
| --- | --- | --- | --- | --- |
| 628 | `500778` / `4` | 0 | 2 | Clave duplicada en `n` (filas 627 y 628). `n+1` aporta `0.05 * 30 = 1.5`. La referencia sumo ese mismo aporte a **las dos** filas (627: `30 + 1.5 -> 32`; 628: `0 + 1.5 -> 2`), contando el aporte dos veces. La herramienta lo aplica solo a la primera aparicion, segun la regla acordada. |
| 868 | `901035` / `9` | 136 | 135 | `n` tiene 10. `n+1` aporta por tipo distinto (`tipo 4`, 2500 -> 125) y por coincidencia exacta (`tipo 9`, 10 -> 0.5). Total `135.5 -> 136`. La referencia dejo 135, es decir descarto el aporte fraccionario del cruce exacto. |

Ambos casos se consideran **correcciones manuales de la referencia**, no defectos del
algoritmo. Si en el futuro se decide replicar el criterio de la referencia, habria que
cambiar dos reglas: propagar el aporte a todas las filas con clave duplicada y truncar
en lugar de aplicar techo cuando hay aportes mixtos.

## 8. Salida esperada del proceso

Para el caso C12/C13 el resultado debe tener 1467 filas de datos, 48 columnas
identicas al archivo base / a `n+1` segun corresponda, y `AO` numerico entero.
