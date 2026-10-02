---
name: leer-facturas-ubl
description: "Reads UBL 2.1 electronic invoices — DIAN Colombia XML/ZIP (incl. AttachedDocument) or PEPPOL / EN 16931 Invoice, CreditNote, DebitNote — into a Power BI star schema (Parquet/CSV) and answers totals, IVA/VAT, credit-note netting or per-supplier questions, always via the pinned ubl-star CLI, never a hand-written XML parser. Use when the user has a folder of invoice .xml/.zip files or mentions «factura electrónica», «XML de la DIAN», «facturas a Power BI», «nota crédito», «CUFE», «UBL», «PEPPOL», «e-invoice», «invoices to Parquet». Not for PDFs/scans, nor for issuing or signing invoices."
---

# Leer facturas UBL con ubl-star

`ubl-star` lee el XML firmado de la factura —la fuente legal, no su PDF— y escribe
un esquema estrella. Es lectura exacta: sin OCR y sin modelo. Para obtener las
cifras, usa siempre la CLI fijada. **Nunca** escribas un parser propio de XML ni
deduzcas un campo que no venga en el documento.

## 1. Comprobar la entrada

- Sirven archivos `.xml` y `.zip` (el adjunto de la DIAN) o carpetas que los
  contengan. Facturas, notas crédito y notas débito.
- Un PDF o un escaneo **no** sirven. Dilo y pide el XML o el ZIP: llega adjunto al
  correo del proveedor o se descarga del portal de la DIAN. No intentes leer el PDF.

## 2. Ejecutar la CLI fijada

```bash
uvx --from "git+https://github.com/CSalcedoDataBI/ubl-star@v0.2.2" ubl-star model <rutas...> --salida <carpeta>
```

- Escribe en `<carpeta>`: `dim_proveedor`, `dim_item`, `dim_fecha`, `fact_factura`,
  `fact_factura_linea` (Parquet por defecto; `--formato csv` para CSV) y `rechazados.csv`.
- Si el usuario no da carpeta, usa `./ubl-star-salida`. Los archivos con el mismo
  nombre se sobrescriben.
- Usa siempre la versión fijada (`@v0.2.2`), nunca una rama.
- Sin `uv`: `pip install "git+https://github.com/CSalcedoDataBI/ubl-star@v0.2.2"`
  y después `ubl-star model ...` (o `python -m ubl_star model ...`).
- Requiere `git` y Python ≥ 3.11. Si la instalación falla, muestra el error y para:
  **no** lo sustituyas con código propio que lea el XML.

Código de salida: `0` = se leyó todo. `1` = hubo archivos rechazados; las tablas
se escriben igual con el resto, así que lee `rechazados.csv` y explica los
motivos. `2` = error de uso (una ruta que no existe o ningún XML/ZIP).

## 3. Responder preguntas sobre las tablas

Agrega con `Decimal`, nunca con `float`, en el mismo entorno fijado. pyarrow ya
viene con el paquete. Escribe el script en una carpeta temporal, no en la del
usuario:

```bash
uv run --no-project --with "ubl-star @ git+https://github.com/CSalcedoDataBI/ubl-star@v0.2.2" python script.py
```

- **Qué columna:** «el total» de un documento es `total` (con impuestos); «cuánto
  se paga» es `pagadero`; el IVA es `impuesto_total`.
- **Las notas crédito restan.** Los importes vienen en positivo; `signo` vale `-1`
  en `nota_credito` y `+1` en factura y `nota_debito`. Neto = `SUM(columna * signo)`
  (`total`, `impuesto_total` o, por línea, `importe`).
- Agrupa **por `moneda`**: nunca sumes COP con EUR. Una moneda vacía va aparte.
- Un documento repetido ya se descartó (está en `rechazados.csv` como duplicado).
  No lo vuelvas a sumar.

Columnas, relaciones para Power BI, qué columna usar en cada pregunta y un ejemplo
de IVA neto: `references/tablas.md`.

## 4. Privacidad

Las facturas reales llevan nombres, NIT y cédulas. Por defecto, entrega archivos y
agregados. Si el usuario pide un listado por documento, dalo con las columnas que
pidió, pero no muestres datos del cliente (`cliente_*`) salvo que los pida.
