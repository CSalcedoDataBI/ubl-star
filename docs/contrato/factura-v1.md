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

Una factura *cuadra* cuando `total == subtotal + impuesto_total` dentro de una
tolerancia de `0.02`, y cuando `fecha_vencimiento >= fecha_emision`. Una línea
cuadra cuando `importe == cantidad * precio_unitario` con la misma tolerancia.

Que cuadre no significa que los valores sean correctos: significa que el
documento es consistente consigo mismo.

**Descuentos y anticipos no entran en esa identidad.** En UBL, lo que se paga es
`LineExtensionAmount + TaxAmount − AllowanceTotalAmount + ChargeTotalAmount −
PrepaidAmount`. El campo `total` del contrato es el total **con impuestos y antes
de descuentos**; lo pagadero vive en `extras`. Meter el pagadero en `total`
convertiría cada subsidio en un descuadre falso.

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
  orden_compra: str | null
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
