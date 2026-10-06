"""Perfil PEPPOL BIS Billing 3.0 / EN 16931: el mismo parser, otras rutas opcionales.

La tesis del proyecto es que un solo parser cubre DIAN y PEPPOL porque lo que
cambia son extensiones y campos fiscales, no la estructura. Estos tests la ponen
a prueba justo en las rutas donde PEPPOL difiere del perfil DIAN.
"""

from datetime import date
from decimal import Decimal

import pytest

from tests.fixtures.generar import (
    construir_peppol_credit_note,
    construir_peppol_invoice,
    construir_peppol_invoice_descuento,
)
from ubl_star.parser import desanidar, parsear
from ubl_star.schema import Invoice


@pytest.fixture
def factura() -> Invoice:
    return parsear(desanidar(construir_peppol_invoice()))


@pytest.fixture
def nota() -> Invoice:
    return parsear(desanidar(construir_peppol_credit_note()))


def test_el_iva_en_moneda_de_contabilidad_no_se_suma_dos_veces() -> None:
    """EN 16931 BT-111: un segundo TaxTotal con el mismo IVA en otra moneda.

    Es el mismo impuesto expresado en la moneda de contabilidad (`TaxCurrencyCode`),
    no un segundo tributo: sumarlo inflaria `impuesto_total`.
    """
    xml = construir_peppol_invoice().replace(
        "<cac:LegalMonetaryTotal>",
        '<cac:TaxTotal><cbc:TaxAmount currencyID="SEK">2400.00</cbc:TaxAmount></cac:TaxTotal>'
        "<cac:LegalMonetaryTotal>",
    )
    factura = parsear(xml)
    assert factura.impuesto_total == Decimal("210.00")
    assert [t["codigo"] for t in factura.extras["impuestos"]] == ["VAT"]
    assert factura.cuadra()


def test_cabecera(factura: Invoice) -> None:
    assert factura.tipo_documento == "factura"
    assert factura.numero_factura == "INV-0001"
    assert factura.fecha_emision == date(2026, 3, 2)
    assert factura.moneda == "EUR"
    assert factura.cufe is None  # PEPPOL no tiene CUFE: ausente, no inventado


def test_el_vencimiento_se_lee_de_cbc_due_date(factura: Invoice) -> None:
    """En Invoice, EN 16931 (BT-9) lo pone en cbc:DueDate, no en PaymentMeans."""
    assert factura.fecha_vencimiento == date(2026, 4, 1)


def test_en_la_nota_credito_el_vencimiento_va_en_payment_means(nota: Invoice) -> None:
    """CreditNote no tiene cbc:DueDate; BT-9 vive en PaymentMeans/PaymentDueDate."""
    assert nota.fecha_vencimiento == date(2026, 4, 1)


def test_la_orden_de_compra_se_lee_de_order_reference(factura: Invoice) -> None:
    assert factura.orden_compra == "PO-0001"


def test_el_id_fiscal_es_el_iva_no_el_registro_mercantil(factura: Invoice) -> None:
    """PartyTaxScheme/CompanyID es el IVA (BT-31); PartyLegalEntity/CompanyID es el
    registro mercantil (BT-30). El contrato pide el id fiscal."""
    assert factura.proveedor_nombre == "EXAMPLE SUPPLIER B.V."
    assert factura.proveedor_id_fiscal == "NL000000000B01"
    assert factura.cliente_nombre == "EXAMPLE BUYER GMBH"
    assert factura.cliente_id_fiscal == "DE000000000"


def test_totales(factura: Invoice) -> None:
    assert factura.subtotal == Decimal("1000.00")
    assert factura.impuesto_total == Decimal("210.00")
    assert factura.total == Decimal("1210.00")
    assert factura.cuadra(), factura.problemas()


def test_sin_description_la_linea_toma_el_nombre_del_articulo(factura: Invoice) -> None:
    """En PEPPOL cbc:Name es obligatorio (BT-153) y cbc:Description opcional (BT-154).
    Si hay Description, manda; si no, el nombre."""
    assert factura.lineas[0].descripcion == "EXAMPLE WIDGET"
    assert factura.lineas[1].descripcion == "EXAMPLE SUPPORT HOURS"


def test_sin_codigo_estandar_la_linea_toma_el_del_vendedor(factura: Invoice) -> None:
    """BT-157 (StandardItemIdentification) es opcional; BT-155 (Sellers) es el habitual."""
    assert [linea.codigo for linea in factura.lineas] == ["SKU-0001", "SKU-0002"]


def test_lineas(factura: Invoice) -> None:
    primera = factura.lineas[0]
    assert primera.cantidad == Decimal("4")
    assert primera.precio_unitario == Decimal("200.00")
    assert primera.importe == Decimal("800.00")
    assert primera.extras["unidad"] == "C62"


def test_la_nota_credito_peppol(nota: Invoice) -> None:
    assert nota.tipo_documento == "nota_credito"
    assert nota.numero_factura == "CN-0001"
    assert nota.total == Decimal("1210.00")
    assert len(nota.lineas) == 2
    assert nota.extras["referencia_factura"] == {
        "numero_factura": "INV-0001",
        "cufe": None,
        "fecha_emision": date(2026, 3, 2),
    }


# --- Descuento de documento (issue #21) --------------------------------------


@pytest.fixture
def con_descuento() -> Invoice:
    return parsear(desanidar(construir_peppol_invoice_descuento()))


def test_lee_el_descuento_y_el_cargo_de_documento(con_descuento: Invoice) -> None:
    assert con_descuento.descuento_total == Decimal("100.00")
    assert con_descuento.cargo_total == Decimal("0.00")


def test_una_factura_peppol_con_descuento_de_documento_cuadra(con_descuento: Invoice) -> None:
    """TaxInclusiveAmount (1089) ya descuenta los 100: no es un descuadre."""
    assert con_descuento.subtotal == Decimal("1000.00")
    assert con_descuento.total == Decimal("1089.00")
    assert con_descuento.cuadra(), con_descuento.problemas()
