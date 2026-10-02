# Contrato de salida — factura v1

Este documento **es** el contrato. Cualquier implementación que lea facturas de
cualquier fuente —XML UBL, PDF nativo, escaneado— y produzca estas tablas con
estos campos es intercambiable aguas abajo con `ubl-star`, sin compartir una
línea de código.

`tests/test_contrato.py` falla si el modelo de este repo se aparta del bloque de
abajo. Ese test es la única razón por la que este documento no se queda viejo.

## Versión

`1`. Un cambio que quite un campo, le cambie el tipo o le cambie el nombre es
**ruptura** y sube a v2. Añadir un campo opcional no rompe: un consumidor que no
lo conoce lo ignora.

## Reglas transversales

- **El dinero es `Decimal`.** El contrato rechaza `float` en cualquier importe.
- **Un campo ausente es `None`**, nunca un cero, nunca una cadena vacía, nunca un
  valor inferido.
- **`extras` es el cajón de lo que no es canónico.** Campos propios del emisor o
  del perfil fiscal van ahí y no sueltos en el modelo, para que el contrato siga
  siendo cerrado.

## Coherencia

Una factura *cuadra* cuando su `total` cumple una de las dos identidades del
estándar, dentro de una tolerancia de `0.02`, y cuando `fecha_vencimiento >=
fecha_emision`:

- **DIAN:** `total == subtotal + impuesto_total`.
- **EN 16931 / PEPPOL** (BT-112), solo si el documento declara `descuento_total` o
  `cargo_total`: `total == subtotal − descuento_total + cargo_total +
  impuesto_total`.

`descuento_total` y `cargo_total` son los descuentos y cargos **de documento**
(`AllowanceTotalAmount` / `ChargeTotalAmount`), tal como vienen. Los añadió v1 sin
romperla: son campos opcionales nuevos. Una línea
cuadra cuando `importe == cantidad * precio_unitario` con la misma tolerancia.

Que cuadre no significa que los valores sean correctos: significa que el
documento es consistente consigo mismo.

**El total es `TaxInclusiveAmount`, y el estándar se aplica de dos maneras.** La
DIAN lo calcula antes de los descuentos de documento: un subsidio solo resta en
lo pagadero. EN 16931 lo calcula después. Por eso se aceptan las dos identidades,
y una factura PEPPOL con descuento de cabecera no aparece como descuadre. Los
anticipos no entran en ninguna de las dos. Lo que se paga vive en
`extras["ubl_payable_amount"]`: meterlo en `total` convertiría cada subsidio en
un descuadre falso.

## Notas crédito y débito

Una nota crédito o débito usa el mismo contrato que una factura. Lo que las
distingue es `tipo_documento`, con tres valores posibles: `factura`,
`nota_credito` y `nota_debito`.

**Los importes van tal como vienen en el documento, en positivo.** Una nota
crédito no llega con signo negativo, y el contrato no se lo inventa. Quien suma
—un total por proveedor, por mes o por año— **resta** las filas con
`tipo_documento = nota_credito`. Si no lo hace, cada devolución o anulación
infla el total en vez de descontarlo.

La factura que corrige la nota va en `extras["referencia_factura"]`, con
`numero_factura`, `cufe` y `fecha_emision`. En una factura, ese valor es `None`.

Añadir `tipo_documento` no rompe v1: es un campo opcional nuevo.

## Campos

```yaml
invoice:
  numero_factura: str | null
  cufe: str | null
  fecha_emision: date | null
  fecha_vencimiento: date | null
  proveedor_nombre: str | null
  proveedor_id_fiscal: str | null
  cliente_nombre: str | null
  cliente_id_fiscal: str | null
  moneda: str | null
  subtotal: money | null
  impuesto_total: money | null
  total: money | null
  descuento_total: money | null
  cargo_total: money | null
  orden_compra: str | null
  tipo_documento: tipo_documento | null
  lineas: list[invoice_line]
  extras: dict
invoice_line:
  descripcion: str | null
  cantidad: money | null
  precio_unitario: money | null
  importe: money | null
  codigo: str | null
  extras: dict
```
