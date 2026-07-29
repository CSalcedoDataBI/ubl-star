# ubl-star

**De factura electrónica UBL 2.1 a hechos listos para analizar.**

Donde la factura electrónica es obligatoria, el documento legal **no es el PDF: es el XML**. El PDF
es su representación gráfica — una foto del original. Leer el XML no es una optimización, es leer la
fuente: **100% de precisión, cero OCR, cero tokens, cero modelo.**

`ubl-star` toma ese XML y entrega `dim_proveedor`, `dim_fecha`, `dim_item` y `fact_factura_linea` en
Parquet, listos para un Lakehouse.

> Estado: recién iniciado. El diseño se está escribiendo.

## Por qué existe

Todo el esfuerzo de la industria está en leer el PDF: OCR, layout, modelos de visión, plantillas por
proveedor. Es trabajo real y difícil — pero en muchos países se está resolviendo un problema que ya
venía resuelto en el adjunto.

- **Colombia (DIAN)** — la factura se emite en XML UBL 2.1, firmada con certificado p12 y validada
  por los servicios web de la DIAN antes de llegar al receptor. El CUFE la identifica.
- **Europa (PEPPOL / EN 16931)** — el mismo UBL 2.1 como sintaxis de la factura electrónica
  transfronteriza.

Un solo parser cubre ambos. Lo que cambia entre jurisdicciones son las extensiones y los campos
fiscales, no la estructura del documento.

## Cómo funciona

1. **Entrada** — un XML UBL 2.1, o el ZIP del adjunto que lo contiene.
2. **Parseo** — sin adivinar: cada campo sale de su ruta en el estándar.
3. **Mapeo** — al contrato de factura canónico (emisor, receptor, líneas, impuestos, totales).
4. **Modelo** — esquema estrella → Parquet / CSV.

No hay escalón caro porque no hay ambigüedad que resolver. Si un campo no está en el XML, no está —
y eso se reporta, no se inventa.

## Relación con `pdfstar`

`ubl-star` es el camino exacto; [`pdfstar`](https://github.com/CSalcedoDataBI/pdfstar) es el camino
degradado para cuando solo hay un PDF (emisor extranjero, factura anterior a la obligatoriedad,
escaneo suelto). Comparten el contrato de datos y el modelo dimensional a propósito: **la salida de
ambos debe ser indistinguible aguas abajo.**

## Licencia

MIT. Solo dependencias permisivas (MIT / Apache-2.0 / BSD) — el mismo criterio que `pdfstar`.

---

© Cristobal Salcedo · [CSalcedoDataBI](https://csalcedodatabi.com/)
