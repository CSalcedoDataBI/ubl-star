"""La CLI: `ubl-star model <xml|zip|carpeta>... --salida DIR`."""

import csv
import shutil
import subprocess
import sys
from pathlib import Path

import pyarrow.parquet as pq
import pytest

import ubl_star
from tests.fixtures.generar import FIXTURES
from ubl_star.cli import main
from ubl_star.modelo import TABLAS

DIRECTORIO = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def buzon(tmp_path: Path) -> Path:
    carpeta = tmp_path / "buzon"
    carpeta.mkdir()
    for nombre in FIXTURES:
        shutil.copy(DIRECTORIO / nombre, carpeta / nombre)
    return carpeta


def test_escribe_las_tablas_en_parquet(
    buzon: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    salida = tmp_path / "salida"
    assert main(["model", str(buzon), "--salida", str(salida)]) == 0
    for tabla in TABLAS:
        assert (salida / f"{tabla}.parquet").is_file(), tabla
    assert pq.read_table(salida / "fact_factura_linea.parquet").num_rows == 10
    assert (salida / "rechazados.csv").is_file()


def test_tambien_escribe_csv(buzon: Path, tmp_path: Path) -> None:
    salida = tmp_path / "salida"
    assert main(["model", str(buzon), "--salida", str(salida), "--formato", "csv"]) == 0
    with (salida / "fact_factura.csv").open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    assert len(filas) == 5
    peppol = next(f for f in filas if f["numero_factura"] == "INV-0001")
    assert peppol["total"] == "1210.000000"


def test_la_salida_estandar_solo_lleva_conteos_nunca_datos(
    buzon: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Lo que imprime la CLI puede acabar en una conversacion con un modelo. Con
    facturas reales, nombres, NIT e importes se quedan en los archivos."""
    main(["model", str(buzon), "--salida", str(tmp_path / "salida")])
    salida = capsys.readouterr().out
    assert "5 documentos" in salida
    assert "10 lineas" in salida
    for dato in ("EXAMPLE", "800111222", "NL000000000B01", "1210", "DEE00000001", "PERSONA"):
        assert dato not in salida, dato


def test_con_rechazos_termina_en_1_y_los_lista_en_csv(
    buzon: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (buzon / "otra_cosa.xml").write_text("<?xml version='1.0'?><OtraCosa/>", encoding="utf-8")
    salida = tmp_path / "salida"
    assert main(["model", str(buzon), "--salida", str(salida)]) == 1
    with (salida / "rechazados.csv").open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    assert [Path(f["archivo"]).name for f in filas] == ["otra_cosa.xml"]
    assert "1 rechazados" in capsys.readouterr().out


def test_una_ruta_que_no_existe_es_un_error_de_uso(tmp_path: Path) -> None:
    assert main(["model", str(tmp_path / "no-existe"), "--salida", str(tmp_path / "s")]) == 2


def test_sin_documentos_es_un_error_de_uso(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vacia = tmp_path / "vacia"
    vacia.mkdir()
    assert main(["model", str(vacia), "--salida", str(tmp_path / "s")]) == 2
    assert "ningun XML ni ZIP" in capsys.readouterr().err


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as salida:
        main(["--version"])
    assert salida.value.code == 0
    assert ubl_star.__version__ in capsys.readouterr().out


def test_se_puede_invocar_como_modulo(buzon: Path, tmp_path: Path) -> None:
    """`python -m ubl_star` es lo que llama el plugin si el script no esta en PATH."""
    resultado = subprocess.run(
        [sys.executable, "-m", "ubl_star", "model", str(buzon), "--salida", str(tmp_path / "s")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stderr
    assert "5 documentos" in resultado.stdout
