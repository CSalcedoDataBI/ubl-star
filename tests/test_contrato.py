"""El modelo no se aparta del documento del contrato.

Este test es la razon por la que docs/contrato/factura-v1.md no se queda viejo:
si alguien anade un campo al modelo y no al documento, esto falla.
"""

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from ubl_star.schema import Dinero, Invoice, InvoiceLine

CONTRATO = Path(__file__).resolve().parents[1] / "docs" / "contrato" / "factura-v1.md"

# Vocabulario de tipos que usa el bloque yaml del documento, traducido a la
# anotacion que pydantic debe ver en el modelo. `Dinero` es
# `Annotated[Decimal, BeforeValidator(...)]`: se compara contra el alias, no
# contra una reconstruccion a mano, porque la metadata del validador tiene que
# coincidir tambien.
_TIPOS_DECLARADOS: dict[str, Any] = {
    "str | null": str | None,
    "date | null": date | None,
    "money | null": Dinero | None,
    "dict": dict[str, Any],
    "list[invoice_line]": list[InvoiceLine],
}


def _campos_declarados() -> dict[str, dict[str, str]]:
    """Lee el unico bloque yaml del documento del contrato."""
    texto = CONTRATO.read_text(encoding="utf-8")
    bloques = re.findall(r"```yaml\n(.*?)```", texto, re.DOTALL)
    assert len(bloques) == 1, f"se esperaba exactamente un bloque yaml, hay {len(bloques)}"
    return yaml.safe_load(bloques[0])


def _tipo_esperado(tipo_declarado: str) -> Any:
    """Traduce un tipo del documento a la anotacion que debe llevar el modelo.

    Un tipo que este mapa no reconoce es un error de documentacion (alguien
    escribio un tipo que el contrato no sabe verificar) y este test debe
    reventar diciendo cual, no ignorarlo en silencio.
    """
    if tipo_declarado not in _TIPOS_DECLARADOS:
        raise AssertionError(
            f"tipo declarado en el contrato sin traduccion conocida: {tipo_declarado!r}. "
            "Añadelo a _TIPOS_DECLARADOS en este test o corrige el documento."
        )
    return _TIPOS_DECLARADOS[tipo_declarado]


def _verifica_tipos(modelo: type[BaseModel], declarados: dict[str, str]) -> None:
    """Compara, campo a campo, el tipo que pide el documento contra el real del modelo."""
    for nombre, tipo_declarado in declarados.items():
        esperado = _tipo_esperado(tipo_declarado)
        real = modelo.model_fields[nombre].annotation
        assert real == esperado, (
            f"{modelo.__name__}.{nombre} anota {real!r} pero el contrato declara "
            f"{tipo_declarado!r} (deberia ser {esperado!r})"
        )


def test_invoice_tiene_exactamente_los_campos_del_contrato() -> None:
    declarados = set(_campos_declarados()["invoice"])
    assert set(Invoice.model_fields) == declarados


def test_invoice_line_tiene_exactamente_los_campos_del_contrato() -> None:
    declarados = set(_campos_declarados()["invoice_line"])
    assert set(InvoiceLine.model_fields) == declarados


def test_invoice_tiene_los_tipos_del_contrato() -> None:
    """No basta con el nombre: un campo que cambia de tipo tambien es ruptura."""
    declarados = _campos_declarados()["invoice"]
    _verifica_tipos(Invoice, declarados)


def test_invoice_line_tiene_los_tipos_del_contrato() -> None:
    declarados = _campos_declarados()["invoice_line"]
    _verifica_tipos(InvoiceLine, declarados)
