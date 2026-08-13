"""La fixture en disco es exactamente lo que produce el generador.

Si alguien la edita a mano, esto lo dice. Es tambien lo que garantiza que no se
cuele un valor real dentro de un archivo que parece sintetico.
"""

from pathlib import Path

from tests.fixtures.generar import construir_adjunto_spd

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_la_fixture_coincide_con_su_generador() -> None:
    en_disco = (FIXTURES / "dian_spd_601.xml").read_text(encoding="utf-8")
    assert en_disco == construir_adjunto_spd()
