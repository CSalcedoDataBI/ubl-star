"""Fabrica las fixtures sinteticas. Ningun valor de aqui es real.

Se genera por codigo y no se escribe a mano para que sea evidente que cada NIT,
cada nombre y cada importe salio de esta funcion y no de la factura de nadie.

La estructura si es la de verdad: AttachedDocument con el Invoice embebido en
CDATA, notas por `languageLocaleID`, subsidios como AllowanceCharge de cabecera
y lineas con `InvoicedQuantity` fija en 1.00 llevando el importe entero en
`PriceAmount`. Eso ultimo es lo que caracteriza al Documento Equivalente SPD
(CustomizationID 601): el XML lleva la plata por concepto, no el consumo fisico.
"""

import json
import sys
from collections.abc import Callable
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


# --- Perfil PEPPOL BIS Billing 3.0 / EN 16931 ------------------------------
#
# Todo inventado: los nombres llevan EXAMPLE, los IVA son ceros con el prefijo
# de pais y el endpoint usa un esquema "0000" que no existe. La estructura es la
# de PEPPOL: Invoice suelto (sin AttachedDocument), vencimiento en `cbc:DueDate`,
# IVA en `PartyTaxScheme/CompanyID` (y el registro mercantil, distinto, en
# `PartyLegalEntity/CompanyID`), el nombre del articulo en `cac:Item/cbc:Name` y
# el codigo del vendedor en `SellersItemIdentification`.
_PEPPOL_INVOICE = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" \
xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" \
xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">\
<cbc:CustomizationID>\
urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0\
</cbc:CustomizationID>\
<cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>\
<cbc:ID>INV-0001</cbc:ID>\
<cbc:IssueDate>2026-03-02</cbc:IssueDate>\
<cbc:DueDate>2026-04-01</cbc:DueDate>\
<cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>\
<cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>\
<cbc:BuyerReference>REF-0001</cbc:BuyerReference>\
<cac:OrderReference><cbc:ID>PO-0001</cbc:ID></cac:OrderReference>\
<cac:AccountingSupplierParty><cac:Party>\
<cbc:EndpointID schemeID="0000">0000000001</cbc:EndpointID>\
<cac:PartyName><cbc:Name>EXAMPLE SUPPLIER</cbc:Name></cac:PartyName>\
<cac:PostalAddress><cac:Country><cbc:IdentificationCode>NL</cbc:IdentificationCode>\
</cac:Country></cac:PostalAddress>\
<cac:PartyTaxScheme><cbc:CompanyID>NL000000000B01</cbc:CompanyID>\
<cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:PartyTaxScheme>\
<cac:PartyLegalEntity><cbc:RegistrationName>EXAMPLE SUPPLIER B.V.</cbc:RegistrationName>\
<cbc:CompanyID>00000001</cbc:CompanyID></cac:PartyLegalEntity>\
</cac:Party></cac:AccountingSupplierParty>\
<cac:AccountingCustomerParty><cac:Party>\
<cbc:EndpointID schemeID="0000">0000000002</cbc:EndpointID>\
<cac:PostalAddress><cac:Country><cbc:IdentificationCode>DE</cbc:IdentificationCode>\
</cac:Country></cac:PostalAddress>\
<cac:PartyTaxScheme><cbc:CompanyID>DE000000000</cbc:CompanyID>\
<cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:PartyTaxScheme>\
<cac:PartyLegalEntity><cbc:RegistrationName>EXAMPLE BUYER GMBH</cbc:RegistrationName>\
</cac:PartyLegalEntity>\
</cac:Party></cac:AccountingCustomerParty>\
<cac:PaymentMeans><cbc:PaymentMeansCode>30</cbc:PaymentMeansCode></cac:PaymentMeans>\
<cac:TaxTotal><cbc:TaxAmount currencyID="EUR">210.00</cbc:TaxAmount>\
<cac:TaxSubtotal><cbc:TaxableAmount currencyID="EUR">1000.00</cbc:TaxableAmount>\
<cbc:TaxAmount currencyID="EUR">210.00</cbc:TaxAmount>\
<cac:TaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>21</cbc:Percent>\
<cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:TaxCategory>\
</cac:TaxSubtotal></cac:TaxTotal>\
<cac:LegalMonetaryTotal>\
<cbc:LineExtensionAmount currencyID="EUR">1000.00</cbc:LineExtensionAmount>\
<cbc:TaxExclusiveAmount currencyID="EUR">1000.00</cbc:TaxExclusiveAmount>\
<cbc:TaxInclusiveAmount currencyID="EUR">1210.00</cbc:TaxInclusiveAmount>\
<cbc:PayableAmount currencyID="EUR">1210.00</cbc:PayableAmount>\
</cac:LegalMonetaryTotal>\
<cac:InvoiceLine><cbc:ID>1</cbc:ID>\
<cbc:InvoicedQuantity unitCode="C62">4</cbc:InvoicedQuantity>\
<cbc:LineExtensionAmount currencyID="EUR">800.00</cbc:LineExtensionAmount>\
<cac:Item><cbc:Name>EXAMPLE WIDGET</cbc:Name>\
<cac:SellersItemIdentification><cbc:ID>SKU-0001</cbc:ID></cac:SellersItemIdentification>\
<cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>21</cbc:Percent>\
<cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:ClassifiedTaxCategory></cac:Item>\
<cac:Price><cbc:PriceAmount currencyID="EUR">200.00</cbc:PriceAmount></cac:Price>\
</cac:InvoiceLine>\
<cac:InvoiceLine><cbc:ID>2</cbc:ID>\
<cbc:InvoicedQuantity unitCode="HUR">2</cbc:InvoicedQuantity>\
<cbc:LineExtensionAmount currencyID="EUR">200.00</cbc:LineExtensionAmount>\
<cac:Item><cbc:Description>EXAMPLE SUPPORT HOURS</cbc:Description>\
<cbc:Name>SUPPORT</cbc:Name>\
<cac:SellersItemIdentification><cbc:ID>SKU-0002</cbc:ID></cac:SellersItemIdentification>\
<cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>21</cbc:Percent>\
<cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:ClassifiedTaxCategory></cac:Item>\
<cac:Price><cbc:PriceAmount currencyID="EUR">100.00</cbc:PriceAmount></cac:Price>\
</cac:InvoiceLine>\
</Invoice>"""


def construir_peppol_invoice() -> str:
    """Una factura PEPPOL BIS 3.0 suelta, como llega por la red PEPPOL."""
    return _PEPPOL_INVOICE


def construir_peppol_credit_note() -> str:
    """La nota credito PEPPOL que anula la factura anterior.

    En CreditNote no existe `cbc:DueDate`: el vencimiento va en
    `cac:PaymentMeans/cbc:PaymentDueDate`.
    """
    return (
        _PEPPOL_INVOICE.replace(":xsd:Invoice-2", ":xsd:CreditNote-2")
        .replace("<Invoice ", "<CreditNote ")
        .replace("</Invoice>", "</CreditNote>")
        .replace("InvoiceLine>", "CreditNoteLine>")
        .replace("InvoicedQuantity", "CreditedQuantity")
        .replace("<cbc:ID>INV-0001</cbc:ID>", "<cbc:ID>CN-0001</cbc:ID>", 1)
        .replace("<cbc:DueDate>2026-04-01</cbc:DueDate>", "")
        .replace(
            "<cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>",
            "<cbc:CreditNoteTypeCode>381</cbc:CreditNoteTypeCode>",
        )
        .replace(
            "</cac:OrderReference>",
            "</cac:OrderReference><cac:BillingReference><cac:InvoiceDocumentReference>"
            "<cbc:ID>INV-0001</cbc:ID><cbc:IssueDate>2026-03-02</cbc:IssueDate>"
            "</cac:InvoiceDocumentReference></cac:BillingReference>",
        )
        .replace(
            "<cbc:PaymentMeansCode>30</cbc:PaymentMeansCode>",
            "<cbc:PaymentMeansCode>30</cbc:PaymentMeansCode>"
            "<cbc:PaymentDueDate>2026-04-01</cbc:PaymentDueDate>",
        )
    )


def construir_peppol_invoice_descuento() -> str:
    """La factura PEPPOL con un descuento de documento de 100 (BT-92).

    En EN 16931 el descuento ya resta en TaxExclusiveAmount (BT-109 = 1000 - 100
    = 900) y por tanto en TaxInclusiveAmount (BT-112 = 900 + 189 = 1089). Es la
    forma que la identidad `total = subtotal + impuesto` de la DIAN no cubre.
    """
    return (
        _PEPPOL_INVOICE.replace("<cbc:ID>INV-0001</cbc:ID>", "<cbc:ID>INV-0002</cbc:ID>", 1)
        .replace(
            "<cac:TaxTotal>",
            "<cac:AllowanceCharge><cbc:ChargeIndicator>false</cbc:ChargeIndicator>"
            "<cbc:AllowanceChargeReason>EXAMPLE DISCOUNT</cbc:AllowanceChargeReason>"
            '<cbc:Amount currencyID="EUR">100.00</cbc:Amount>'
            "<cac:TaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>21</cbc:Percent>"
            "<cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:TaxCategory>"
            "</cac:AllowanceCharge><cac:TaxTotal>",
            1,
        )
        .replace(">210.00</cbc:TaxAmount>", ">189.00</cbc:TaxAmount>")
        .replace(
            '<cbc:TaxableAmount currencyID="EUR">1000.00</cbc:TaxableAmount>',
            '<cbc:TaxableAmount currencyID="EUR">900.00</cbc:TaxableAmount>',
        )
        .replace(
            '<cbc:TaxExclusiveAmount currencyID="EUR">1000.00</cbc:TaxExclusiveAmount>',
            '<cbc:TaxExclusiveAmount currencyID="EUR">900.00</cbc:TaxExclusiveAmount>',
        )
        .replace(
            '<cbc:TaxInclusiveAmount currencyID="EUR">1210.00</cbc:TaxInclusiveAmount>',
            '<cbc:TaxInclusiveAmount currencyID="EUR">1089.00</cbc:TaxInclusiveAmount>'
            '<cbc:AllowanceTotalAmount currencyID="EUR">100.00</cbc:AllowanceTotalAmount>'
            '<cbc:ChargeTotalAmount currencyID="EUR">0.00</cbc:ChargeTotalAmount>',
        )
        .replace(
            '<cbc:PayableAmount currencyID="EUR">1210.00</cbc:PayableAmount>',
            '<cbc:PayableAmount currencyID="EUR">1089.00</cbc:PayableAmount>',
        )
    )


def _nota_credito_dian() -> str:
    return construir_adjunto_nota("CreditNote")


def _nota_debito_dian() -> str:
    return construir_adjunto_nota("DebitNote")


# Cada fixture en disco y la funcion que la fabrica. `test_fixtures` comprueba
# que coinciden byte a byte y que la salida del parser coincide con `golden/`.
FIXTURES: dict[str, Callable[[], str]] = {
    "dian_spd_601.xml": construir_adjunto_spd,
    "dian_nota_credito.xml": _nota_credito_dian,
    "dian_nota_debito.xml": _nota_debito_dian,
    "peppol_invoice.xml": construir_peppol_invoice,
    "peppol_credit_note.xml": construir_peppol_credit_note,
    "peppol_invoice_descuento.xml": construir_peppol_invoice_descuento,
}

GOLDEN = AQUI / "golden"


def golden(nombre: str) -> Path:
    """`peppol_invoice.xml` -> `golden/peppol_invoice.json`."""
    return GOLDEN / (Path(nombre).stem + ".json")


def escribir_golden() -> None:
    """Regenera los golden files con el parser ACTUAL.

    Solo se corre a proposito (`python -m tests.fixtures.generar --golden`), y
    el diff que deja es lo que hay que leer: un golden que cambia es un cambio
    en la salida del parser.
    """
    from ubl_star.parser import desanidar, parsear

    GOLDEN.mkdir(exist_ok=True)
    for nombre, construir in FIXTURES.items():
        salida = parsear(desanidar(construir())).model_dump(mode="json")
        texto = json.dumps(salida, indent=2, sort_keys=True, ensure_ascii=False)
        golden(nombre).write_text(texto + "\n", encoding="utf-8")
        print(f"escrito golden/{golden(nombre).name}")


def main() -> None:
    for nombre, construir in FIXTURES.items():
        (AQUI / nombre).write_text(construir(), encoding="utf-8")
        print(f"escrita {nombre}")
    if "--golden" in sys.argv:
        escribir_golden()


if __name__ == "__main__":
    main()
