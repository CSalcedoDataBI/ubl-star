"""Las fixtures en disco son exactamente lo que produce el generador.

Si alguien las edita a mano, esto lo dice. Es tambien lo que garantiza que no se
cuele un valor real dentro de un archivo que parece sintetico.
"""

import json
from pathlib import Path

import pytest

from tests.fixtures.generar import FIXTURES, golden
from ubl_star.parser import leer

DIRECTORIO = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.parametrize("nombre", sorted(FIXTURES))
def test_la_fixture_coincide_con_su_generador(nombre: str) -> None:
    en_disco = (DIRECTORIO / nombre).read_text(encoding="utf-8")
    assert en_disco == FIXTURES[nombre]()


@pytest.mark.parametrize("nombre", sorted(FIXTURES))
def test_la_salida_del_parser_coincide_con_su_golden(nombre: str) -> None:
    """La salida completa, campo por campo, leida desde el archivo en disco.

    Un fallo aqui es un cambio observable en la salida. Si es deliberado, se
    regenera con `python -m tests.fixtures.generar --golden` y el diff del
    golden se revisa en el PR.
    """
    esperado = json.loads(golden(nombre).read_text(encoding="utf-8"))
    assert leer(DIRECTORIO / nombre).model_dump(mode="json") == esperado


def test_no_hay_fixtures_huerfanas() -> None:
    """Un XML en fixtures/ que el generador no fabrica no tiene origen demostrable."""
    en_disco = {p.name for p in DIRECTORIO.glob("*.xml")}
    assert en_disco == set(FIXTURES)


def test_cada_fixture_tiene_su_golden_y_ninguno_sobra() -> None:
    en_disco = {p.name for p in golden("x.xml").parent.glob("*.json")}
    assert en_disco == {golden(n).name for n in FIXTURES}
