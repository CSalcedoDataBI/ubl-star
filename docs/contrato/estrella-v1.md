# Contrato de salida — esquema estrella v1

Lo que produce `ubl-star model`: cinco tablas en Parquet (o CSV), listas para
cargar en Power BI o en cualquier motor que lea Parquet. Igual que
[`factura-v1.md`](factura-v1.md), este documento **es** el contrato:
`tests/test_estrella.py` falla si las tablas que se escriben se apartan del
bloque de abajo.

## Versión

`1`. Quitar una columna, cambiarle el tipo o el nombre es **ruptura** y sube a
v2. Añadir una columna no rompe.

## Las tablas

| Tabla | Grano | Clave |
|---|---|---|
| `dim_proveedor` | un emisor | `proveedor_key` |
| `dim_item` | un artículo (código + descripción) | `item_key` |
| `dim_fecha` | un día | `fecha_key` (`AAAAMMDD`) |
| `fact_factura` | un documento (factura o nota) | `numero_factura` + `proveedor_key` + `tipo_documento` |
| `fact_factura_linea` | una línea de un documento | `numero_factura` + `proveedor_key` + `tipo_documento` + `linea_numero` |

Relaciones: `fact_* .proveedor_key → dim_proveedor`, `fact_factura_linea.item_key
→ dim_item`, `fact_* .fecha_emision_key` y `fecha_vencimiento_key → dim_fecha`.
Toda clave de un hecho existe en su dimensión (`tests/test_estrella.py` lo
verifica).

## Reglas

- **Las claves sustitutas son estables dentro de una corrida**, no entre corridas:
  se numeran desde 1 en el orden de la clave natural. Para unir dos cargas, usar
  la clave natural (`proveedor_id_fiscal`, `codigo` + `descripcion`, `fecha`).
- **Clave natural del proveedor:** `proveedor_id_fiscal`. Si el documento no lo
  trae, el nombre. El nombre que se guarda es el del primer documento leído (los
  archivos se leen en orden de ruta).
- **Clave natural del artículo:** `codigo` + `descripcion`. El mismo código con
  otra descripción es otro artículo: el código de un vendedor no es universal.
- **`dim_fecha` cubre años completos**, del 1 de enero del primer año al 31 de
  diciembre del último en el que cae alguna fecha de emisión o vencimiento. Así
  sirve como tabla de fechas de Power BI, que exige un rango contiguo.
- **El dinero es `decimal(38, 6)`.** Un importe con más de 6 decimales no se
  redondea: el archivo se rechaza y queda en `rechazados.csv`.
- **`signo`** vale `-1` en las notas crédito y `1` en facturas y notas débito.
  Los importes van en positivo, como vienen en el XML (ver `factura-v1.md`); el
  neto es `SUM(importe * signo)`.
- **Un documento repetido se cuenta una vez.** Si el mismo `tipo_documento` +
  proveedor + `numero_factura` llega dos veces (por ejemplo, en el ZIP y suelto),
  el segundo se rechaza como duplicado.
- **Lo que no se puede leer no se cuela.** Cada archivo rechazado queda en
  `rechazados.csv` con su motivo, y la CLI termina con código 1.

## Columnas

Tipos: `int` es entero de 64 bits, `str` texto, `date` fecha, `money` es
`decimal(38, 6)`. `| null` marca las columnas que pueden venir vacías.

```yaml
dim_proveedor:
  proveedor_key: int
  proveedor_id_fiscal: str | null
  proveedor_nombre: str | null
dim_item:
  item_key: int
  codigo: str | null
  descripcion: str | null
dim_fecha:
  fecha_key: int
  fecha: date
  anio: int
  trimestre: int
  mes: int
  dia: int
fact_factura:
  numero_factura: str | null
  cufe: str | null
  tipo_documento: str
  signo: int
  proveedor_key: int
  cliente_id_fiscal: str | null
  cliente_nombre: str | null
  fecha_emision_key: int | null
  fecha_vencimiento_key: int | null
  moneda: str | null
  orden_compra: str | null
  subtotal: money | null
  impuesto_total: money | null
  total: money | null
  pagadero: money | null
  archivo: str
fact_factura_linea:
  numero_factura: str | null
  tipo_documento: str
  signo: int
  linea_numero: int
  proveedor_key: int
  item_key: int
  fecha_emision_key: int | null
  moneda: str | null
  cantidad: money | null
  precio_unitario: money | null
  importe: money | null
  unidad: str | null
```
