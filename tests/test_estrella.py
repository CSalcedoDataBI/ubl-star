"""El esquema estrella: lo que `ubl-star model` escribe, anclado a su contrato.

Todo se construye desde las fixtures sinteticas de `tests/fixtures/`: tres
documentos DIAN (factura, nota credito, nota debito) y dos PEPPOL (factura,
nota credito), dos lineas cada uno.
"""

import re
import shutil
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml

from tests.fixtures.generar import FIXTURES, construir_peppol_invoice
from ubl_star.modelo import TABLAS, Modelo, construir, escribir

DIRECTORIO = Path(__file__).resolve().parent / "fixtures"
CONTRATO = Path(__file__).resolve().parents[1] / "docs" / "contrato" / "estrella-v1.md"

_TIPOS: dict[str, pa.DataType] = {
    "int": pa.int64(),
    "str": pa.string(),
    "date": pa.date32(),
    "money": pa.decimal128(38, 6),
}


def _declaradas() -> dict[str, dict[str, str]]:
    texto = CONTRATO.read_text(encoding="utf-8")
    bloques = re.findall(r"```yaml\n(.*?)```", texto, re.DOTALL)
    assert len(bloques) == 1, f"se esperaba exactamente un bloque yaml, hay {len(bloques)}"
    return yaml.safe_load(bloques[0])


@pytest.fixture
def entrada(tmp_path: Path) -> Path:
    carpeta = tmp_path / "buzon"
    carpeta.mkdir()
    for nombre in FIXTURES:
        shutil.copy(DIRECTORIO / nombre, carpeta / nombre)
    return carpeta


@pytest.fixture
def modelo(entrada: Path) -> Modelo:
    return construir([entrada])


def _filas(modelo: Modelo, tabla: str) -> list[dict[str, Any]]:
    filas: list[dict[str, Any]] = modelo.tablas[tabla].to_pylist()
    return filas


# --- Contrato ----------------------------------------------------------------


def test_las_tablas_son_las_del_contrato() -> None:
    assert set(TABLAS) == set(_declaradas())


@pytest.mark.parametrize("tabla", sorted(_declaradas()))
def test_cada_tabla_tiene_las_columnas_y_tipos_del_contrato(modelo: Modelo, tabla: str) -> None:
    esquema = modelo.tablas[tabla].schema
    declaradas = _declaradas()[tabla]
    assert esquema.names == list(declaradas), "columnas u orden distintos al contrato"
    for columna, tipo in declaradas.items():
        nulable = tipo.endswith("| null")
        base = tipo.removesuffix("| null").strip()
        campo = esquema.field(columna)
        assert campo.type == _TIPOS[base], f"{tabla}.{columna}: {campo.type} != {base}"
        assert campo.nullable == nulable, f"{tabla}.{columna}: nullable={campo.nullable}"


def test_lo_escrito_en_parquet_conserva_el_esquema(modelo: Modelo, tmp_path: Path) -> None:
    escribir(modelo, tmp_path / "salida")
    for tabla in TABLAS:
        leida = pq.read_table(tmp_path / "salida" / f"{tabla}.parquet")
        assert leida.schema.equals(modelo.tablas[tabla].schema), tabla


# --- Contenido ---------------------------------------------------------------


def test_cuenta_documentos_y_lineas(modelo: Modelo) -> None:
    assert modelo.tablas["fact_factura"].num_rows == 5
    assert modelo.tablas["fact_factura_linea"].num_rows == 10
    assert modelo.leidos == 5
    assert modelo.rechazados == []


def test_un_proveedor_por_id_fiscal(modelo: Modelo) -> None:
    proveedores = {f["proveedor_id_fiscal"]: f for f in _filas(modelo, "dim_proveedor")}
    assert set(proveedores) == {"800111222", "NL000000000B01"}
    assert proveedores["NL000000000B01"]["proveedor_nombre"] == "EXAMPLE SUPPLIER B.V."
    assert sorted(f["proveedor_key"] for f in proveedores.values()) == [1, 2]


def test_las_notas_credito_restan(modelo: Modelo) -> None:
    signos = {
        (f["tipo_documento"], f["numero_factura"]): f["signo"]
        for f in _filas(modelo, "fact_factura")
    }
    assert signos[("factura", "DEE00000001")] == 1
    assert signos[("nota_credito", "NC00000001")] == -1
    assert signos[("nota_debito", "ND00000001")] == 1
    assert signos[("nota_credito", "CN-0001")] == -1


def test_el_neto_por_proveedor_descuenta_las_notas(modelo: Modelo) -> None:
    claves = {f["proveedor_key"]: f["proveedor_id_fiscal"] for f in _filas(modelo, "dim_proveedor")}
    neto: dict[str, Decimal] = {}
    for f in _filas(modelo, "fact_factura_linea"):
        nit = claves[f["proveedor_key"]]
        neto[nit] = neto.get(nit, Decimal(0)) + f["importe"] * f["signo"]
    # DIAN: factura 30000 - nota credito 30000 + nota debito 30000.
    assert neto["800111222"] == Decimal("30000")
    # PEPPOL: factura 1000 anulada por su nota credito.
    assert neto["NL000000000B01"] == Decimal("0")


def test_el_dinero_sale_exacto_en_decimal(modelo: Modelo) -> None:
    factura = next(f for f in _filas(modelo, "fact_factura") if f["numero_factura"] == "INV-0001")
    assert factura["total"] == Decimal("1210.000000")
    assert factura["impuesto_total"] == Decimal("210")
    assert factura["pagadero"] == Decimal("1210")
    assert isinstance(factura["total"], Decimal)


def test_dim_fecha_cubre_anios_completos_y_contiguos(modelo: Modelo) -> None:
    fechas = [f["fecha"] for f in _filas(modelo, "dim_fecha")]
    assert fechas[0] == date(2026, 1, 1)
    assert fechas[-1] == date(2026, 12, 31)
    assert len(fechas) == 365
    primera = _filas(modelo, "dim_fecha")[0]
    assert primera == {
        "fecha_key": 20260101,
        "fecha": date(2026, 1, 1),
        "anio": 2026,
        "trimestre": 1,
        "mes": 1,
        "dia": 1,
    }


def test_toda_clave_de_un_hecho_existe_en_su_dimension(modelo: Modelo) -> None:
    proveedores = {f["proveedor_key"] for f in _filas(modelo, "dim_proveedor")}
    items = {f["item_key"] for f in _filas(modelo, "dim_item")}
    fechas = {f["fecha_key"] for f in _filas(modelo, "dim_fecha")}
    for f in _filas(modelo, "fact_factura"):
        assert f["proveedor_key"] in proveedores
        assert f["fecha_emision_key"] in fechas
        assert f["fecha_vencimiento_key"] is None or f["fecha_vencimiento_key"] in fechas
    for f in _filas(modelo, "fact_factura_linea"):
        assert f["proveedor_key"] in proveedores
        assert f["item_key"] in items
        assert f["fecha_emision_key"] in fechas


def test_las_lineas_se_numeran_desde_uno(modelo: Modelo) -> None:
    lineas = [f for f in _filas(modelo, "fact_factura_linea") if f["numero_factura"] == "INV-0001"]
    assert [f["linea_numero"] for f in lineas] == [1, 2]
    assert lineas[0]["unidad"] == "C62"


def test_el_articulo_se_identifica_por_codigo_y_descripcion(modelo: Modelo) -> None:
    items = {(f["codigo"], f["descripcion"]) for f in _filas(modelo, "dim_item")}
    assert ("SKU-0001", "EXAMPLE WIDGET") in items
    assert ("90", "ENERGIA MDO REGULADO") in items
    # Factura y notas DIAN repiten los mismos dos articulos: no se duplican.
    assert len(items) == 4


def test_la_fecha_de_vencimiento_se_enlaza(modelo: Modelo) -> None:
    factura = next(f for f in _filas(modelo, "fact_factura") if f["numero_factura"] == "INV-0001")
    assert factura["fecha_emision_key"] == 20260302
    assert factura["fecha_vencimiento_key"] == 20260401


# --- Lo que no entra -----------------------------------------------------------


def test_un_documento_repetido_se_cuenta_una_vez(entrada: Path) -> None:
    shutil.copy(entrada / "peppol_invoice.xml", entrada / "zz_copia_de_peppol.xml")
    modelo = construir([entrada])
    assert modelo.tablas["fact_factura"].num_rows == 5
    assert len(modelo.rechazados) == 1
    rechazo = modelo.rechazados[0]
    assert rechazo.archivo.endswith("zz_copia_de_peppol.xml")
    assert "duplicado" in rechazo.motivo
    assert "peppol_invoice.xml" in rechazo.motivo


def test_un_archivo_ilegible_se_rechaza_sin_frenar_los_demas(entrada: Path) -> None:
    (entrada / "otra_cosa.xml").write_text("<?xml version='1.0'?><OtraCosa/>", encoding="utf-8")
    modelo = construir([entrada])
    assert modelo.tablas["fact_factura"].num_rows == 5
    assert [r.archivo.endswith("otra_cosa.xml") for r in modelo.rechazados] == [True]
    assert "NoEsUnaFactura" in modelo.rechazados[0].motivo


def test_un_importe_con_mas_de_seis_decimales_se_rechaza_no_se_redondea(tmp_path: Path) -> None:
    xml = construir_peppol_invoice().replace(
        ">200.00</cbc:PriceAmount>", ">200.0000001</cbc:PriceAmount>"
    )
    ruta = tmp_path / "decimales.xml"
    ruta.write_text(xml, encoding="utf-8")
    modelo = construir([ruta])
    assert modelo.tablas["fact_factura"].num_rows == 0
    assert "200.0000001" in modelo.rechazados[0].motivo


def test_solo_lee_xml_y_zip_y_en_orden(entrada: Path) -> None:
    (entrada / "leeme.txt").write_text("no soy una factura", encoding="utf-8")
    sub = entrada / "sub"
    sub.mkdir()
    shutil.copy(entrada / "peppol_credit_note.xml", sub / "A.XML")
    modelo = construir([entrada])
    # El .txt se ignora; el .XML en mayuscula de la subcarpeta se lee (y es un duplicado).
    assert modelo.leidos == 6
    assert [r.archivo.endswith("A.XML") for r in modelo.rechazados] == [True]


def test_sin_documentos_las_tablas_salen_vacias_con_su_esquema(tmp_path: Path) -> None:
    modelo = construir([tmp_path])
    for tabla in TABLAS:
        assert modelo.tablas[tabla].num_rows == 0
        assert modelo.tablas[tabla].schema.names == list(_declaradas()[tabla])
