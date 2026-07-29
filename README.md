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

## Alcance — y lo que queda fuera a propósito

`ubl-star` lee **XML**. Si lo que tienes es un PDF escaneado, una foto o un PDF sin adjunto, esta no
es tu herramienta: la lectura óptica es otro problema, con otro costo, otra tasa de error y otra
forma de auditarse. **Mezclar los dos caminos es lo que hace que un extractor de facturas no se pueda
verificar** — cuando un campo puede venir de una ruta exacta del estándar o de un modelo que lo
adivinó, ya no sabes cuál de las dos ocurrió.

Aquí solo pasa lo primero. Un campo que no está en el XML se reporta ausente.

## El contrato de salida

Las tablas, las columnas y las claves que produce `ubl-star` están declaradas en un **contrato
versionado**, y hay un test que ancla la salida a ese documento. La razón es que otra herramienta
—leyendo otra fuente— pueda entregar exactamente el mismo modelo y ser intercambiable aguas abajo,
sin compartir una línea de código con esta.

## Licencia

MIT. Solo dependencias permisivas (MIT / Apache-2.0 / BSD) — el mismo criterio que `pdfstar`.

---

© Cristobal Salcedo · [CSalcedoDataBI](https://csalcedodatabi.com/)
