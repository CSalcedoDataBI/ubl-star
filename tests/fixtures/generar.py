"""Fabrica las fixtures sinteticas. Ningun valor de aqui es real.

Se genera por codigo y no se escribe a mano para que sea evidente que cada NIT,
cada nombre y cada importe salio de esta funcion y no de la factura de nadie.

La estructura si es la de verdad: AttachedDocument con el Invoice embebido en
CDATA, notas por `languageLocaleID`, subsidios como AllowanceCharge de cabecera
y lineas con `InvoicedQuantity` fija en 1.00 llevando el importe entero en
`PriceAmount`. Eso ultimo es lo que caracteriza al Documento Equivalente SPD
(CustomizationID 601): el XML lleva la plata por concepto, no el consumo fisico.
"""

from pathlib import Path
from xml.sax.saxutils import escape

AQUI = Path(__file__).resolve().parent

# Todo inventado. NIT 800.111.222 y cedula 10000001 no corresponden a nadie.
_INVOICE = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" \
xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" \
xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">\
<cbc:UBLVersionID>UBL 2.1</cbc:UBLVersionID>\
<cbc:CustomizationID>601</cbc:CustomizationID>\
<cbc:ProfileID>DIAN 2.1: Documento Equivalente SPD</cbc:ProfileID>\
<cbc:ID>DEE00000001</cbc:ID>\
<cbc:UUID schemeID="1" schemeName="CUDE-SHA384">abc123def456</cbc:UUID>\
<cbc:IssueDate>2026-01-15</cbc:IssueDate>\
<cbc:IssueTime>04:00:00-05:00</cbc:IssueTime>\
<cbc:InvoiceTypeCode>60</cbc:InvoiceTypeCode>\
<cbc:Note languageLocaleID="contrato">99999999</cbc:Note>\
<cbc:Note languageLocaleID="corte">17</cbc:Note>\
<cbc:Note languageLocaleID="Cuota Financiacion">1000.00</cbc:Note>\
<cbc:DocumentCurrencyCode>COP</cbc:DocumentCurrencyCode>\
<cbc:LineCountNumeric>2</cbc:LineCountNumeric>\
<cac:AccountingSupplierParty><cac:Party>\
<cac:PartyTaxScheme><cbc:RegistrationName>SERVICIOS PUBLICOS EJEMPLO E.S.P.</cbc:RegistrationName>\
<cbc:CompanyID schemeID="1" schemeName="31">800111222</cbc:CompanyID>\
</cac:PartyTaxScheme>\
<cac:PartyLegalEntity><cbc:RegistrationName>SERVICIOS PUBLICOS EJEMPLO E.S.P.</cbc:RegistrationName>\
<cbc:CompanyID schemeID="1" schemeName="31">800111222</cbc:CompanyID>\
</cac:PartyLegalEntity></cac:Party></cac:AccountingSupplierParty>\
<cac:AccountingCustomerParty><cbc:CustomerAssignedAccountID>99999999</cbc:CustomerAssignedAccountID>\
<cac:Party>\
<cac:PartyLegalEntity><cbc:RegistrationName>PERSONA DE PRUEBA</cbc:RegistrationName>\
<cbc:CompanyID schemeID="0" schemeName="13">10000001</cbc:CompanyID>\
</cac:PartyLegalEntity></cac:Party></cac:AccountingCustomerParty>\
<cac:PaymentMeans><cbc:ID>2</cbc:ID><cbc:PaymentMeansCode>ZZZ</cbc:PaymentMeansCode>\
<cbc:PaymentDueDate>2026-02-05</cbc:PaymentDueDate></cac:PaymentMeans>\
<cac:AllowanceCharge><cbc:ID schemeName="2">1</cbc:ID>\
<cbc:ChargeIndicator>false</cbc:ChargeIndicator>\
<cbc:AllowanceChargeReasonCode>01</cbc:AllowanceChargeReasonCode>\
<cbc:AllowanceChargeReason>SUBSIDIO</cbc:AllowanceChargeReason>\
<cbc:MultiplierFactorNumeric>10.00</cbc:MultiplierFactorNumeric>\
<cbc:Amount currencyID="COP">3000.00</cbc:Amount>\
<cbc:BaseAmount currencyID="COP">30190.00</cbc:BaseAmount></cac:AllowanceCharge>\
<cac:TaxTotal><cbc:TaxAmount currencyID="COP">190.00</cbc:TaxAmount>\
<cac:TaxSubtotal><cbc:TaxableAmount currencyID="COP">1000.00</cbc:TaxableAmount>\
<cbc:TaxAmount currencyID="COP">190.00</cbc:TaxAmount>\
<cac:TaxCategory><cbc:Percent>19.00</cbc:Percent>\
<cac:TaxScheme><cbc:ID>01</cbc:ID><cbc:Name>IVA</cbc:Name></cac:TaxScheme>\
</cac:TaxCategory></cac:TaxSubtotal></cac:TaxTotal>\
<cac:LegalMonetaryTotal>\
<cbc:LineExtensionAmount currencyID="COP">30000.00</cbc:LineExtensionAmount>\
<cbc:TaxExclusiveAmount currencyID="COP">1000.00</cbc:TaxExclusiveAmount>\
<cbc:TaxInclusiveAmount currencyID="COP">30190.00</cbc:TaxInclusiveAmount>\
<cbc:AllowanceTotalAmount currencyID="COP">3000.00</cbc:AllowanceTotalAmount>\
<cbc:ChargeTotalAmount currencyID="COP">0.00</cbc:ChargeTotalAmount>\
<cbc:PrepaidAmount currencyID="COP">0.00</cbc:PrepaidAmount>\
<cbc:PayableRoundingAmount currencyID="COP">0.00</cbc:PayableRoundingAmount>\
<cbc:PayableAmount currencyID="COP">27190.00</cbc:PayableAmount>\
</cac:LegalMonetaryTotal>\
<cac:InvoiceLine><cbc:ID schemeID="0">1</cbc:ID>\
<cbc:InvoicedQuantity unitCode="KWH">1.00</cbc:InvoicedQuantity>\
<cbc:LineExtensionAmount currencyID="COP">20000.00</cbc:LineExtensionAmount>\
<cbc:AccountingCostCode>111111111</cbc:AccountingCostCode>\
<cac:Item><cbc:Description>ENERGIA MDO REGULADO</cbc:Description>\
<cac:StandardItemIdentification><cbc:ID schemeID="999">90</cbc:ID>\
</cac:StandardItemIdentification></cac:Item>\
<cac:Price><cbc:PriceAmount currencyID="COP">20000.00</cbc:PriceAmount>\
<cbc:BaseQuantity unitCode="KWH">1.00</cbc:BaseQuantity></cac:Price></cac:InvoiceLine>\
<cac:InvoiceLine><cbc:ID schemeID="0">2</cbc:ID>\
<cbc:InvoicedQuantity unitCode="MTQ">1.00</cbc:InvoicedQuantity>\
<cbc:LineExtensionAmount currencyID="COP">10000.00</cbc:LineExtensionAmount>\
<cbc:AccountingCostCode>222222222</cbc:AccountingCostCode>\
<cac:Item><cbc:Description>AGUA POTABLE</cbc:Description>\
<cac:StandardItemIdentification><cbc:ID schemeID="999">87</cbc:ID>\
</cac:StandardItemIdentification></cac:Item>\
<cac:Price><cbc:PriceAmount currencyID="COP">10000.00</cbc:PriceAmount>\
<cbc:BaseQuantity unitCode="MTQ">1.00</cbc:BaseQuantity></cac:Price></cac:InvoiceLine>\
</Invoice>"""


def _adjuntar(documento: str, numero: str) -> str:
    """Envuelve un documento UBL en un AttachedDocument, en CDATA, como la DIAN."""
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        "<AttachedDocument "
        'xmlns="urn:oasis:names:specification:ubl:schema:xsd:AttachedDocument-2" '
        'xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" '
        'xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">'
        "<cbc:ID>" + numero + "</cbc:ID>"
        "<cac:Attachment><cac:ExternalReference>"
        "<cbc:Description><![CDATA[" + documento + "]]></cbc:Description>"
        "</cac:ExternalReference></cac:Attachment>"
        "</AttachedDocument>"
    )


def construir_adjunto_spd() -> str:
    """El AttachedDocument con el Invoice embebido en CDATA, como lo emite la DIAN."""
    return _adjuntar(_INVOICE, "DEE00000001")


def construir_adjunto_escapado() -> str:
    """El mismo AttachedDocument, con el Invoice escapado con entidades y sin CDATA.

    Para un parser XML es el mismo texto que la version en CDATA; para una
    busqueda de cadena no, porque `<Invoice` aparece como `&lt;Invoice`.
    """
    return construir_adjunto_spd().replace("<![CDATA[" + _INVOICE + "]]>", escape(_INVOICE))


def construir_invoice_prefijado() -> str:
    """El Invoice suelto con la raiz prefijada: `<inv:Invoice xmlns:inv=...>`.

    Es el mismo elemento que `<Invoice xmlns=...>`, solo que con otro prefijo.
    """
    return _INVOICE.replace('<Invoice xmlns="urn:', '<inv:Invoice xmlns:inv="urn:', 1).replace(
        "</Invoice>", "</inv:Invoice>"
    )


# La factura que corrige la nota. Mismos datos sinteticos que _INVOICE.
_REFERENCIA = (
    "<cac:BillingReference><cac:InvoiceDocumentReference>"
    "<cbc:ID>DEE00000001</cbc:ID>"
    '<cbc:UUID schemeName="CUDE-SHA384">abc123def456</cbc:UUID>'
    "<cbc:IssueDate>2026-01-15</cbc:IssueDate>"
    "</cac:InvoiceDocumentReference></cac:BillingReference>"
)


def construir_nota(raiz: str) -> str:
    """Una CreditNote o DebitNote suelta, derivada del mismo Invoice sintetico.

    Cambia solo lo que el estandar cambia: la raiz y su espacio de nombres, las
    lineas (`CreditNoteLine` / `CreditedQuantity`, `DebitNoteLine` /
    `DebitedQuantity`), el codigo de tipo, la referencia a la factura corregida
    y, en la DebitNote, los totales en `RequestedMonetaryTotal`.
    """
    sufijo = {"CreditNote": "Credited", "DebitNote": "Debited"}[raiz]
    tipo = "<cbc:CreditNoteTypeCode>91</cbc:CreditNoteTypeCode>" if raiz == "CreditNote" else ""
    nota = (
        _INVOICE.replace(":xsd:Invoice-2", f":xsd:{raiz}-2")
        .replace("<Invoice ", f"<{raiz} ")
        .replace("</Invoice>", f"</{raiz}>")
        .replace("InvoiceLine>", f"{raiz}Line>")
        .replace("InvoicedQuantity", f"{sufijo}Quantity")
        .replace("<cbc:InvoiceTypeCode>60</cbc:InvoiceTypeCode>", tipo)
        .replace("<cbc:ID>DEE00000001</cbc:ID>", f"<cbc:ID>{_numero_nota(raiz)}</cbc:ID>")
        .replace("<cac:AccountingSupplierParty>", _REFERENCIA + "<cac:AccountingSupplierParty>")
    )
    if raiz == "DebitNote":
        nota = nota.replace("LegalMonetaryTotal>", "RequestedMonetaryTotal>")
    return nota


def _numero_nota(raiz: str) -> str:
    return {"CreditNote": "NC00000001", "DebitNote": "ND00000001"}[raiz]


def construir_adjunto_nota(raiz: str) -> str:
    """La nota dentro de un AttachedDocument, como llega en el buzon."""
    return _adjuntar(construir_nota(raiz), _numero_nota(raiz))


def main() -> None:
    (AQUI / "dian_spd_601.xml").write_text(construir_adjunto_spd(), encoding="utf-8")
    print("escrita dian_spd_601.xml")


if __name__ == "__main__":
    main()
