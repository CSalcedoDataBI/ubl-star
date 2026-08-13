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


def test_un_campo_ausente_es_none_no_cero() -> None:
    assert Invoice().total is None
