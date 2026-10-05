# Las tablas de `ubl-star model`

Resumen para consultar. El contrato completo, con tipos y reglas, está en
<https://github.com/CSalcedoDataBI/ubl-star/blob/v0.2.6/docs/contrato/estrella-v1.md>.

| Tabla | Grano | Columnas útiles |
|---|---|---|
| `dim_proveedor` | un emisor | `proveedor_key`, `proveedor_id_fiscal` (NIT / IVA), `proveedor_nombre` |
| `dim_item` | código + descripción | `item_key`, `codigo`, `descripcion` |
| `dim_fecha` | un día (años completos) | `fecha_key` (AAAAMMDD), `fecha`, `anio`, `trimestre`, `mes`, `dia` |
| `fact_factura` | un documento | `numero_factura`, `cufe`, `tipo_documento`, `signo`, `proveedor_key`, `cliente_*`, `fecha_emision_key`, `fecha_vencimiento_key`, `moneda`, `orden_compra`, `subtotal`, `impuesto_total`, `total`, `pagadero`, `archivo` |
| `fact_factura_linea` | una línea | `numero_factura`, `tipo_documento`, `signo`, `linea_numero`, `proveedor_key`, `item_key`, `fecha_emision_key`, `moneda`, `cantidad`, `precio_unitario`, `importe`, `unidad` |

## Reglas que cambian una cifra

- `tipo_documento`: `factura`, `nota_credito` o `nota_debito`. `signo` = `-1`
  solo en la nota crédito.
- `total` es `TaxInclusiveAmount`, es decir, base más impuestos. En la DIAN va
  **antes** de los descuentos de documento; en PEPPOL / EN 16931 ya los descuenta.
  Para saber cuánto se paga (después de descuentos, subsidios y anticipos), usa
  siempre `pagadero`.
- El dinero es `decimal(38, 6)`. Léelo como `Decimal` (`to_pylist()` en pyarrow ya
  lo devuelve así).
- Un campo vacío es un dato que **no estaba en el XML**. Nunca es un cero.
- `dim_fecha` cubre años completos: sirve tal cual como tabla de fechas en Power BI.

## Relaciones para Power BI

`fact_*[proveedor_key] → dim_proveedor`, `fact_factura_linea[item_key] →
dim_item`, `fact_*[fecha_emision_key] → dim_fecha[fecha_key]` (activa) y
`fact_factura[fecha_vencimiento_key] → dim_fecha[fecha_key]` (inactiva).

## Ejemplo: IVA neto por moneda

```python
from collections import defaultdict
from decimal import Decimal

import pyarrow.parquet as pq

neto: dict[str, Decimal] = defaultdict(Decimal)
for f in pq.read_table("salida/fact_factura.parquet").to_pylist():
    if f["impuesto_total"] is not None:
        neto[f["moneda"]] += f["impuesto_total"] * f["signo"]
for moneda, valor in sorted(neto.items()):
    print(moneda, valor)
```
