"""El parser: cada campo por su ruta del estandar, sin adivinar."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from tests.fixtures.generar import construir_adjunto_spd
from ubl_star.parser import NoEsUnaFactura, desanidar, leer, parsear


@pytest.fixture
def factura():
    return parsear(desanidar(construir_adjunto_spd()))


def test_desanida_el_invoice_del_attached_document() -> None:
    interno = desanidar(construir_adjunto_spd())
    assert "<Invoice" in interno
    assert "AttachedDocument" not in interno


def test_un_invoice_suelto_pasa_sin_tocarlo() -> None:
    interno = desanidar(construir_adjunto_spd())
    assert desanidar(interno) == interno


def test_un_xml_que_no_es_factura_lo_dice() -> None:
    with pytest.raises(NoEsUnaFactura):
        desanidar("<?xml version='1.0'?><OtraCosa/>")


def test_cabecera(factura) -> None:
    assert factura.numero_factura == "DEE00000001"
    assert factura.cufe == "abc123def456"
    assert factura.fecha_emision == date(2026, 1, 15)
    assert factura.fecha_vencimiento == date(2026, 2, 5)
    assert factura.moneda == "COP"


def test_partes(factura) -> None:
    assert factura.proveedor_nombre == "SERVICIOS PUBLICOS EJEMPLO E.S.P."
    assert factura.proveedor_id_fiscal == "800111222"
    assert factura.cliente_nombre == "PERSONA DE PRUEBA"
    assert factura.cliente_id_fiscal == "10000001"


def test_totales_en_decimal(factura) -> None:
    assert factura.subtotal == Decimal("30000.00")
    assert factura.impuesto_total == Decimal("190.00")
    assert factura.total == Decimal("30190.00")
    assert isinstance(factura.total, Decimal)


def test_la_factura_cuadra_consigo_misma(factura) -> None:
    """subtotal + impuesto == total. Los descuentos no entran en esa identidad."""
    assert factura.cuadra(), factura.problemas()


def test_lo_pagadero_va_a_extras_no_a_total(factura) -> None:
    assert factura.extras["ubl_payable_amount"] == Decimal("27190.00")
    assert factura.extras["ubl_allowance_total"] == Decimal("3000.00")


def test_las_notas_del_perfil_spd_van_a_extras(factura) -> None:
    assert factura.extras["notas"]["contrato"] == "99999999"
    assert factura.extras["notas"]["corte"] == "17"
    assert factura.extras["notas"]["Cuota Financiacion"] == "1000.00"


def test_los_subsidios_van_a_extras_con_su_razon(factura) -> None:
    descuentos = factura.extras["descuentos"]
    assert len(descuentos) == 1
    assert descuentos[0]["razon"] == "SUBSIDIO"
    assert descuentos[0]["porcentaje"] == Decimal("10.00")
    assert descuentos[0]["importe"] == Decimal("3000.00")


def test_lineas(factura) -> None:
    assert len(factura.lineas) == 2
    primera = factura.lineas[0]
    assert primera.descripcion == "ENERGIA MDO REGULADO"
    assert primera.codigo == "90"
    assert primera.cantidad == Decimal("1.00")
    assert primera.precio_unitario == Decimal("20000.00")
    assert primera.importe == Decimal("20000.00")


def test_la_unidad_y_la_cuenta_de_la_linea_van_a_extras(factura) -> None:
    assert factura.lineas[0].extras["unidad"] == "KWH"
    assert factura.lineas[0].extras["cuenta"] == "111111111"
    assert factura.lineas[1].extras["unidad"] == "MTQ"


def test_un_campo_opcional_ausente_es_none_no_una_excepcion() -> None:
    """El perfil SPD no trae orden de compra. Ausente es None, no un invento."""
    factura = parsear(desanidar(construir_adjunto_spd()))
    assert factura.orden_compra is None


def test_leer_acepta_la_ruta_de_un_zip(tmp_path: Path) -> None:
    import zipfile

    destino = tmp_path / "adjunto.zip"
    with zipfile.ZipFile(destino, "w") as z:
        z.writestr("ad.xml", construir_adjunto_spd())
        z.writestr("ds.pdf", b"%PDF-1.4")

    assert leer(destino).numero_factura == "DEE00000001"
