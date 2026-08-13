"""El modelo no se aparta del documento del contrato.

Este test es la razon por la que docs/contrato/factura-v1.md no se queda viejo:
si alguien anade un campo al modelo y no al documento, esto falla.
"""

import re
from pathlib import Path

import yaml

from ubl_star.schema import Invoice, InvoiceLine

CONTRATO = Path(__file__).resolve().parents[1] / "docs" / "contrato" / "factura-v1.md"


def _campos_declarados() -> dict[str, dict[str, str]]:
    """Lee el unico bloque yaml del documento del contrato."""
    texto = CONTRATO.read_text(encoding="utf-8")
    bloques = re.findall(r"```yaml\n(.*?)```", texto, re.DOTALL)
    assert len(bloques) == 1, f"se esperaba exactamente un bloque yaml, hay {len(bloques)}"
    return yaml.safe_load(bloques[0])


def test_invoice_tiene_exactamente_los_campos_del_contrato() -> None:
    declarados = set(_campos_declarados()["invoice"])
    assert set(Invoice.model_fields) == declarados


def test_invoice_line_tiene_exactamente_los_campos_del_contrato() -> None:
    declarados = set(_campos_declarados()["invoice_line"])
    assert set(InvoiceLine.model_fields) == declarados
