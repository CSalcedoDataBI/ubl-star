"""El contrato se comporta como dice el documento."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ubl_star.schema import Invoice, InvoiceLine


def test_el_dinero_rechaza_float() -> None:
    with pytest.raises(ValidationError, match="no pasa por float"):
        Invoice(total=1234.56)  # type: ignore[arg-type]


def test_el_dinero_acepta_el_texto_original() -> None:
    assert Invoice(total="1234.56").total == Decimal("1234.56")


def test_un_campo_canonico_mal_escrito_revienta() -> None:
    with pytest.raises(ValidationError):
        Invoice(numero_factra="X-1")  # type: ignore[call-arg]


def test_los_extras_no_revientan() -> None:
    factura = Invoice(extras={"contrato": "99999999"})
    assert factura.extras["contrato"] == "99999999"


def test_total_que_no_cuadra_se_reporta_sin_reventar() -> None:
    factura = Invoice(subtotal="100.00", impuesto_total="19.00", total="200.00")
    problemas = factura.problemas()
    assert len(problemas) == 1
    assert problemas[0].campo == "total"
    assert not factura.cuadra()


def test_total_dentro_de_la_tolerancia_cuadra() -> None:
    factura = Invoice(subtotal="100.00", impuesto_total="18.99", total="119.00")
    assert factura.cuadra()


def test_total_a_exactamente_la_tolerancia_cuadra() -> None:
    """El documento dice 'dentro de una tolerancia de 0.02': el borde exacto cuadra.

    La comparacion en `problemas()` es `>`, no `>=`, asi que una diferencia de
    exactamente TOLERANCIA debe aceptarse, no reportarse.
    """
    factura = Invoice(subtotal="100.00", impuesto_total="19.00", total="119.02")
    assert factura.cuadra()


def test_vencimiento_anterior_a_la_emision_se_reporta() -> None:
    factura = Invoice(fecha_emision=date(2026, 3, 24), fecha_vencimiento=date(2026, 3, 1))
    assert [p.campo for p in factura.problemas()] == ["fecha_vencimiento"]


def test_linea_que_no_cuadra_se_reporta_con_su_indice_humano() -> None:
    factura = Invoice(
        lineas=[
            InvoiceLine(cantidad="1", precio_unitario="10.00", importe="10.00"),
            InvoiceLine(cantidad="2", precio_unitario="10.00", importe="99.00"),
        ]
    )
    assert [p.campo for p in factura.problemas()] == ["lineas[2].linea_importe"]


def test_una_linea_incompleta_no_es_una_incoherencia() -> None:
    """Un hueco es un campo que nadie leyo, no un descuadre."""
    assert InvoiceLine(cantidad="1", importe="10.00").problemas() == []


def test_una_factura_incompleta_no_es_una_incoherencia() -> None:
    """La misma regla, a nivel cabecera: falta impuesto_total, no hay con que comparar.

    Si estan subtotal y total pero falta impuesto_total, no hay problema de
    total que reportar: es un campo que nadie leyo, no un descuadre.
    """
    factura = Invoice(subtotal="100.00", total="119.00")
    assert [p.campo for p in factura.problemas()] == []


def test_un_campo_ausente_es_none_no_cero() -> None:
    assert Invoice().total is None


# --- Coherencia EN 16931 (issue #21) -----------------------------------------
# En EN 16931 el total con impuestos ya descuenta los descuentos de documento:
# BT-112 = BT-106 - BT-107 + BT-108 + BT-110. En la DIAN no: total = subtotal +
# impuesto. Las dos identidades son del estandar; una factura que cumple
# cualquiera de las dos cuadra.


def test_un_descuento_de_documento_en16931_cuadra() -> None:
    factura = Invoice(
        subtotal="1000.00",
        descuento_total="100.00",
        impuesto_total="189.00",
        total="1089.00",
    )
    assert factura.cuadra(), factura.problemas()


def test_un_cargo_de_documento_en16931_cuadra() -> None:
    factura = Invoice(
        subtotal="1000.00", cargo_total="50.00", impuesto_total="220.50", total="1270.50"
    )
    assert factura.cuadra(), factura.problemas()


def test_la_identidad_dian_sigue_cuadrando_con_descuento_declarado() -> None:
    """DIAN: el subsidio esta en AllowanceTotalAmount pero no resta del total."""
    factura = Invoice(
        subtotal="30000.00",
        descuento_total="3000.00",
        impuesto_total="190.00",
        total="30190.00",
    )
    assert factura.cuadra(), factura.problemas()


def test_un_total_que_no_cumple_ninguna_identidad_se_reporta() -> None:
    factura = Invoice(
        subtotal="1000.00",
        descuento_total="100.00",
        impuesto_total="189.00",
        total="1095.00",
    )
    problemas = factura.problemas()
    assert [p.campo for p in problemas] == ["total"]
    assert "1089.00" in problemas[0].detalle  # la cuenta EN 16931 que tampoco cuadra


def test_sin_descuento_declarado_la_identidad_en16931_no_aplica() -> None:
    """Sin descuento_total ni cargo_total, la unica identidad es la de siempre."""
    factura = Invoice(subtotal="1000.00", impuesto_total="189.00", total="1089.00")
    assert not factura.cuadra()
