"""El adjunto: encontrar el XML de la factura entre lo demas."""

import zipfile
from pathlib import Path

import pytest

from tests.fixtures.generar import construir_adjunto_spd
from ubl_star.zip import AdjuntoAmbiguo, SinFacturaEnAdjunto, localizar_xml


def _zip_con(tmp_path: Path, **archivos: bytes) -> Path:
    destino = tmp_path / "adjunto.zip"
    with zipfile.ZipFile(destino, "w") as z:
        for nombre, contenido in archivos.items():
            z.writestr(nombre.replace("__", "."), contenido)
    return destino


def test_un_xml_suelto_se_lee_tal_cual(tmp_path: Path) -> None:
    ruta = tmp_path / "factura.xml"
    ruta.write_text(construir_adjunto_spd(), encoding="utf-8")
    assert localizar_xml(ruta) == construir_adjunto_spd()


def test_encuentra_el_xml_dentro_del_zip(tmp_path: Path) -> None:
    ruta = _zip_con(
        tmp_path,
        ad089__xml=construir_adjunto_spd().encode("utf-8"),
        ds089__pdf=b"%PDF-1.4 no soy un xml",
    )
    assert localizar_xml(ruta) == construir_adjunto_spd()


def test_un_zip_sin_xml_lo_dice(tmp_path: Path) -> None:
    ruta = _zip_con(tmp_path, ds089__pdf=b"%PDF-1.4")
    with pytest.raises(SinFacturaEnAdjunto):
        localizar_xml(ruta)


def test_un_zip_con_dos_xml_no_adivina(tmp_path: Path) -> None:
    """Elegir uno seria inventar. Se reporta y decide quien llama."""
    ruta = _zip_con(
        tmp_path,
        uno__xml=construir_adjunto_spd().encode("utf-8"),
        dos__xml=construir_adjunto_spd().encode("utf-8"),
    )
    with pytest.raises(AdjuntoAmbiguo):
        localizar_xml(ruta)


def test_ignora_lo_que_no_es_xml_ni_por_extension_ni_por_carpeta(tmp_path: Path) -> None:
    ruta = _zip_con(
        tmp_path,
        **{
            "docs/leeme__txt": b"nada",
            "ad089__xml": construir_adjunto_spd().encode("utf-8"),
        },
    )
    assert localizar_xml(ruta) == construir_adjunto_spd()
