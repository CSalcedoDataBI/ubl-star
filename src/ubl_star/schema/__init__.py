"""Los contratos: que es exactamente una factura para ubl-star.

La forma la declara `docs/contrato/factura-v1.md` y `tests/test_contrato.py`
ancla este modulo a ese documento. No se toca uno sin el otro.

El dinero va en `Decimal` y el contrato rechaza `float`: esto termina en
contabilidad y `0.1 + 0.2 != 0.3` en float.
"""

from datetime import date
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

TOLERANCIA = Decimal("0.02")
"""Margen para el redondeo del emisor. No es un descuadre que merezca atencion."""


def _rechaza_float(v: Any) -> Any:
    """Un float ya perdio precision antes de llegar aqui.

    `Decimal(0.1)` no es `0.1`, y pydantic disimula el destrozo convirtiendo el
    float por su repr. Quien tenga un float debe pasar el texto original.
    """
    if isinstance(v, float):
        raise ValueError(
            f"{v!r} es un float y el dinero no pasa por float: usa Decimal o el texto original"
        )
    return v


Dinero = Annotated[Decimal, BeforeValidator(_rechaza_float)]
"""Un importe. Acepta texto, entero o Decimal; nunca float."""


class Problema(BaseModel):
    """Una incoherencia concreta, con el campo al que culpa."""

    campo: str
    detalle: str

    def __str__(self) -> str:
        return f"{self.campo}: {self.detalle}"


class _Base(BaseModel):
    # extra='forbid': un campo canonico mal escrito debe reventar, no colarse.
    # validate_assignment: el contrato vale tambien DESPUES de construir.
    model_config = ConfigDict(populate_by_name=True, extra="forbid", validate_assignment=True)

    extras: dict[str, Any] = Field(default_factory=dict)
    """Campos propios del emisor o del perfil fiscal. Cajon aparte, no sueltos."""


class InvoiceLine(_Base):
    """Una linea de detalle. El grano de `fact_factura_linea`."""

    descripcion: str | None = Field(default=None, alias="linea_descripcion")
    cantidad: Dinero | None = Field(default=None, alias="linea_cantidad")
    precio_unitario: Dinero | None = Field(default=None, alias="linea_precio_unitario")
    importe: Dinero | None = Field(default=None, alias="linea_importe")
    codigo: str | None = Field(default=None, alias="linea_codigo")

    def problemas(self) -> list[Problema]:
        """Incoherencias de la linea. Lista vacia = la linea cuadra."""
        if self.cantidad is None or self.precio_unitario is None or self.importe is None:
            # Un hueco no es una incoherencia: es un campo que nadie leyo.
            return []

        esperado = self.cantidad * self.precio_unitario
        if abs(self.importe - esperado) > TOLERANCIA:
            return [
                Problema(
                    campo="linea_importe",
                    detalle=(
                        f"{self.importe} no cuadra con cantidad x precio_unitario "
                        f"({self.cantidad} x {self.precio_unitario} = {esperado})"
                    ),
                )
            ]
        return []


class Invoice(_Base):
    """Una factura: cabecera + lineas de detalle."""

    numero_factura: str | None = None
    cufe: str | None = None
    fecha_emision: date | None = None
    fecha_vencimiento: date | None = None
    proveedor_nombre: str | None = None
    proveedor_id_fiscal: str | None = None
    cliente_nombre: str | None = None
    cliente_id_fiscal: str | None = None
    moneda: str | None = None
    subtotal: Dinero | None = None
    impuesto_total: Dinero | None = None
    total: Dinero | None = None
    orden_compra: str | None = None

    lineas: list[InvoiceLine] = Field(default_factory=list)

    def problemas(self) -> list[Problema]:
        """Todas las incoherencias de la factura, incluidas las de sus lineas."""
        encontrados: list[Problema] = []

        if self.subtotal is not None and self.impuesto_total is not None and self.total is not None:
            esperado = self.subtotal + self.impuesto_total
            if abs(self.total - esperado) > TOLERANCIA:
                encontrados.append(
                    Problema(
                        campo="total",
                        detalle=(
                            f"{self.total} no cuadra con subtotal + impuesto_total "
                            f"({self.subtotal} + {self.impuesto_total} = {esperado})"
                        ),
                    )
                )

        if self.fecha_emision and self.fecha_vencimiento:
            if self.fecha_vencimiento < self.fecha_emision:
                encontrados.append(
                    Problema(
                        campo="fecha_vencimiento",
                        detalle=(
                            f"{self.fecha_vencimiento} es anterior a la emision "
                            f"({self.fecha_emision})"
                        ),
                    )
                )

        # La linea se numera como la lee un humano en el papel: la primera es la 1.
        for i, linea in enumerate(self.lineas, start=1):
            for p in linea.problemas():
                encontrados.append(Problema(campo=f"lineas[{i}].{p.campo}", detalle=p.detalle))

        return encontrados

    def cuadra(self) -> bool:
        """Atajo legible para el camino feliz."""
        return not self.problemas()
