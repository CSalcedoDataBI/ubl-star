"""XML UBL 2.1 -> el contrato Invoice. Cada campo por su ruta del estandar.

Dos pasos, deliberadamente separados:

- `desanidar` resuelve que la DIAN no entrega el Invoice suelto: lo embebe en
  CDATA dentro de un AttachedDocument junto con la respuesta del validador.
- `parsear` mapea. No calcula, no infiere, no rellena: si un campo no esta en el
  XML, el contrato lo recibe como None.

Se usa defusedxml y no la stdlib a secas porque esto lee documentos que llegan
de un tercero, y `xml.etree` es vulnerable a entidades expansivas.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, ParseError

from defusedxml.ElementTree import fromstring

from ubl_star.schema import Invoice, InvoiceLine, TipoDocumento
from ubl_star.zip import localizar_xml

NS = {
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


# Raiz UBL -> tipo_documento del contrato. Las tres comparten estructura; lo que
# cambia esta en _RUTAS.
TIPOS: dict[str, TipoDocumento] = {
    "Invoice": "factura",
    "CreditNote": "nota_credito",
    "DebitNote": "nota_debito",
}


class NoEsUnaFactura(Exception):
    """El XML no es un Invoice, CreditNote o DebitNote, ni un AttachedDocument que lo contenga."""


def _nombre_local(nodo: Element) -> str:
    """`{urn:...}Invoice` -> `Invoice`. El prefijo del documento no importa."""
    return nodo.tag.rsplit("}", 1)[-1]


def _raiz(xml: str) -> Element | None:
    """La raiz del XML, o None si el texto no es XML bien formado."""
    try:
        raiz: Element = fromstring(xml)
    except ParseError:
        return None
    return raiz


def desanidar(xml: str) -> str:
    """Devuelve el Invoice. Si viene embebido en un AttachedDocument, lo saca.

    Se decide por el elemento y no por el texto: buscar `"<Invoice"` en la cadena
    no ve un Invoice escapado con entidades (`&lt;Invoice`) ni una raiz con
    prefijo (`<inv:Invoice>`), y si ve uno que solo esta en un comentario.

    El AttachedDocument lleva en `cbc:Description` el Invoice y la
    ApplicationResponse del validador. El parser ya entrega ese texto
    desescapado, venga en CDATA o con entidades. Se busca el que sea una factura
    en vez de tomar el primero por posicion, porque el orden no lo garantiza el
    estandar.
    """
    raiz = _raiz(xml)
    if raiz is None:
        raise NoEsUnaFactura("el texto no es XML bien formado")

    if _nombre_local(raiz) in TIPOS:
        return xml

    if _nombre_local(raiz) == "AttachedDocument":
        for descripcion in raiz.iterfind(
            "cac:Attachment/cac:ExternalReference/cbc:Description", NS
        ):
            bloque = (descripcion.text or "").strip()
            embebido = _raiz(bloque)
            if embebido is not None and _nombre_local(embebido) in TIPOS:
                return bloque

    raise NoEsUnaFactura("el XML no es una factura ni una nota, ni contiene una embebida")


def _texto(nodo: Element | None, ruta: str) -> str | None:
    """El texto de una ruta, o None si no esta. Nunca una cadena vacia."""
    if nodo is None:
        return None
    encontrado = nodo.find(ruta, NS)
    if encontrado is None or encontrado.text is None:
        return None
    valor = encontrado.text.strip()
    return valor or None


def _dinero(nodo: Element | None, ruta: str) -> Decimal | None:
    """Un importe como Decimal, leido del texto tal cual esta escrito."""
    crudo = _texto(nodo, ruta)
    return Decimal(crudo) if crudo is not None else None


def _fecha(nodo: Element | None, ruta: str) -> date | None:
    crudo = _texto(nodo, ruta)
    return date.fromisoformat(crudo) if crudo is not None else None


def _atributo(nodo: Element | None, ruta: str, nombre: str) -> str | None:
    if nodo is None:
        return None
    encontrado = nodo.find(ruta, NS)
    return encontrado.get(nombre) if encontrado is not None else None


def _notas(raiz: Element) -> dict[str, str]:
    """Las cbc:Note del perfil SPD, indexadas por su languageLocaleID.

    Ahi es donde EPM pone el contrato, el ciclo de corte y la cuota de
    financiacion: datos que el estandar no tiene donde colocar y que el emisor
    cuelga de una nota etiquetada.
    """
    notas: dict[str, str] = {}
    for nota in raiz.findall("cbc:Note", NS):
        etiqueta = nota.get("languageLocaleID")
        if etiqueta and nota.text:
            notas[etiqueta] = nota.text.strip()
    return notas


def _descuentos(raiz: Element) -> list[dict[str, Any]]:
    """Los AllowanceCharge de cabecera: subsidios, minimo vital, recargos."""
    salida: list[dict[str, Any]] = []
    for cargo in raiz.findall("cac:AllowanceCharge", NS):
        salida.append(
            {
                "id": _texto(cargo, "cbc:ID"),
                "es_recargo": _texto(cargo, "cbc:ChargeIndicator") == "true",
                "codigo_razon": _texto(cargo, "cbc:AllowanceChargeReasonCode"),
                "razon": _texto(cargo, "cbc:AllowanceChargeReason"),
                "porcentaje": _dinero(cargo, "cbc:MultiplierFactorNumeric"),
                "importe": _dinero(cargo, "cbc:Amount"),
                "base": _dinero(cargo, "cbc:BaseAmount"),
            }
        )
    return salida


def _referencia(raiz: Element) -> dict[str, Any] | None:
    """La factura que corrige una nota. None si el documento no la trae."""
    ref = raiz.find("cac:BillingReference/cac:InvoiceDocumentReference", NS)
    if ref is None:
        return None
    return {
        "numero_factura": _texto(ref, "cbc:ID"),
        "cufe": _texto(ref, "cbc:UUID"),
        "fecha_emision": _fecha(ref, "cbc:IssueDate"),
    }


def _linea(nodo: Element, cantidad: str) -> InvoiceLine:
    return InvoiceLine(
        descripcion=_texto(nodo, "cac:Item/cbc:Description"),
        cantidad=_dinero(nodo, cantidad),
        precio_unitario=_dinero(nodo, "cac:Price/cbc:PriceAmount"),
        importe=_dinero(nodo, "cbc:LineExtensionAmount"),
        codigo=_texto(nodo, "cac:Item/cac:StandardItemIdentification/cbc:ID"),
        extras={
            "unidad": _atributo(nodo, cantidad, "unitCode"),
            "cuenta": _texto(nodo, "cbc:AccountingCostCode"),
        },
    )


# Lo unico que cambia entre los tres documentos: (linea, cantidad, totales).
# En DebitNote los totales viven en RequestedMonetaryTotal.
_RUTAS = {
    "Invoice": ("cac:InvoiceLine", "cbc:InvoicedQuantity", "cac:LegalMonetaryTotal"),
    "CreditNote": ("cac:CreditNoteLine", "cbc:CreditedQuantity", "cac:LegalMonetaryTotal"),
    "DebitNote": ("cac:DebitNoteLine", "cbc:DebitedQuantity", "cac:RequestedMonetaryTotal"),
}


def parsear(xml: str) -> Invoice:
    """Mapea un Invoice, CreditNote o DebitNote UBL 2.1 al contrato.

    Lo que no esta, no esta. Los importes de una nota van tal como vienen, en
    positivo: el signo lo da `tipo_documento`.
    """
    raiz = fromstring(xml)

    nombre = _nombre_local(raiz)
    if nombre not in TIPOS:
        raise NoEsUnaFactura(f"la raiz es {raiz.tag}, no un Invoice, CreditNote ni DebitNote")
    ruta_linea, ruta_cantidad, ruta_totales = _RUTAS[nombre]

    proveedor = raiz.find("cac:AccountingSupplierParty/cac:Party", NS)
    cliente = raiz.find("cac:AccountingCustomerParty/cac:Party", NS)
    totales = raiz.find(ruta_totales, NS)

    return Invoice(
        numero_factura=_texto(raiz, "cbc:ID"),
        cufe=_texto(raiz, "cbc:UUID"),
        fecha_emision=_fecha(raiz, "cbc:IssueDate"),
        fecha_vencimiento=_fecha(raiz, "cac:PaymentMeans/cbc:PaymentDueDate"),
        proveedor_nombre=_texto(proveedor, "cac:PartyLegalEntity/cbc:RegistrationName"),
        proveedor_id_fiscal=_texto(proveedor, "cac:PartyLegalEntity/cbc:CompanyID"),
        cliente_nombre=_texto(cliente, "cac:PartyLegalEntity/cbc:RegistrationName"),
        cliente_id_fiscal=_texto(cliente, "cac:PartyLegalEntity/cbc:CompanyID"),
        moneda=_texto(raiz, "cbc:DocumentCurrencyCode"),
        subtotal=_dinero(totales, "cbc:LineExtensionAmount"),
        impuesto_total=_dinero(raiz, "cac:TaxTotal/cbc:TaxAmount"),
        # TaxInclusiveAmount y no PayableAmount: lo pagadero resta descuentos y
        # meterlo aqui convertiria cada subsidio en un descuadre falso. Ver el
        # contrato, seccion "Coherencia".
        total=_dinero(totales, "cbc:TaxInclusiveAmount"),
        tipo_documento=TIPOS[nombre],
        lineas=[_linea(n, ruta_cantidad) for n in raiz.findall(ruta_linea, NS)],
        extras={
            "ubl_customization_id": _texto(raiz, "cbc:CustomizationID"),
            "ubl_profile_id": _texto(raiz, "cbc:ProfileID"),
            "ubl_invoice_type_code": _texto(raiz, "cbc:InvoiceTypeCode"),
            "ubl_tax_exclusive_amount": _dinero(totales, "cbc:TaxExclusiveAmount"),
            "ubl_payable_amount": _dinero(totales, "cbc:PayableAmount"),
            "ubl_allowance_total": _dinero(totales, "cbc:AllowanceTotalAmount"),
            "ubl_charge_total": _dinero(totales, "cbc:ChargeTotalAmount"),
            "ubl_prepaid_amount": _dinero(totales, "cbc:PrepaidAmount"),
            "notas": _notas(raiz),
            "descuentos": _descuentos(raiz),
            "referencia_factura": _referencia(raiz),
        },
    )


def leer(ruta: Path) -> Invoice:
    """El camino completo: ZIP o XML en disco -> contrato."""
    return parsear(desanidar(localizar_xml(Path(ruta))))
