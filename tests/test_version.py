"""El paquete existe y se puede importar."""

import ubl_star


def test_paquete_declara_version() -> None:
    assert isinstance(ubl_star.__version__, str)
    assert ubl_star.__version__
