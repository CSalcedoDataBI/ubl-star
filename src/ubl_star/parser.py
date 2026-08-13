"""XML UBL 2.1 -> el contrato Invoice. Cada campo por su ruta del estandar.

Dos pasos, deliberadamente separados:

- `desanidar` resuelve que la DIAN no entrega el Invoice suelto: lo embebe en
  CDATA dentro de un AttachedDocument junto con la respuesta del validador.
- `parsear` mapea. No calcula, no infiere, no rellena: si un campo no esta en el
  XML, el contrato lo recibe como None.

Se usa defusedxml y no la stdlib a secas porque esto lee documentos que llegan
de un tercero, y `xml.etree` es vulnerable a entidades expansivas.
"""

import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

from defusedxml.ElementTree import fromstring

from ubl_star.schema import Invoice, InvoiceLine
from ubl_star.zip import localizar_xml

NS = {
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}

_CDATA = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.DOTALL)


class NoEsUnaFactura(Exception):
    """El XML no es un Invoice ni un AttachedDocument que lo contenga."""


def desanidar(xml: str) -> str:
    """Devuelve el Invoice. Si viene embebido en un AttachedDocument, lo saca.

    El AttachedDocument lleva dos bloques CDATA: el Invoice y la
    ApplicationResponse del validador. Se busca el que sea una factura en vez de
    tomar el primero por posicion, porque el orden no lo garantiza el estandar.
    """
    if "<Invoice" in xml and "<AttachedDocument" not in xml:
        return xml

    for candidato in _CDATA.findall(xml):
        # findall() esta tipado como list[Any] en typeshed (los grupos podrian
        # no ser str); aqui siempre lo son porque el patron no tiene alternativas.
        bloque: str = candidato
        if "<Invoice" in bloque:
            return bloque

    raise NoEsUnaFactura("el XML no es un Invoice ni contiene uno embebido")


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


def _linea(nodo: Element) -> InvoiceLine:
    return InvoiceLine(
        descripcion=_texto(nodo, "cac:Item/cbc:Description"),
        cantidad=_dinero(nodo, "cbc:InvoicedQuantity"),
        precio_unitario=_dinero(nodo, "cac:Price/cbc:PriceAmount"),
        importe=_dinero(nodo, "cbc:LineExtensionAmount"),
        codigo=_texto(nodo, "cac:Item/cac:StandardItemIdentification/cbc:ID"),
        extras={
            "unidad": _atributo(nodo, "cbc:InvoicedQuantity", "unitCode"),
            "cuenta": _texto(nodo, "cbc:AccountingCostCode"),
        },
    )


def parsear(xml: str) -> Invoice:
    """Mapea un Invoice UBL 2.1 al contrato. Lo que no esta, no esta."""
    raiz = fromstring(xml)

    if not raiz.tag.endswith("}Invoice") and raiz.tag != "Invoice":
        raise NoEsUnaFactura(f"la raiz es {raiz.tag}, no un Invoice")

    proveedor = raiz.find("cac:AccountingSupplierParty/cac:Party", NS)
    cliente = raiz.find("cac:AccountingCustomerParty/cac:Party", NS)
    totales = raiz.find("cac:LegalMonetaryTotal", NS)

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
        lineas=[_linea(n) for n in raiz.findall("cac:InvoiceLine", NS)],
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
        },
    )


def leer(ruta: Path) -> Invoice:
    """El camino completo: ZIP o XML en disco -> contrato."""
    return parsear(desanidar(localizar_xml(Path(ruta))))
