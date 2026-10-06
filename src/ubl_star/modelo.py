"""Facturas -> esquema estrella. El contrato es `docs/contrato/estrella-v1.md`.

Este modulo no lee XML: recibe rutas, llama a `parser.leer` por cada archivo y
arma las tablas. Un archivo que no se puede leer no frena a los demas: queda en
`rechazados` con su motivo, y quien llame decide que hacer con eso.
"""

import csv
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

from ubl_star.parser import leer
from ubl_star.schema import Invoice

ESCALA = 6
"""Decimales del dinero en las tablas. Mas que esto no se redondea: se rechaza."""

_DINERO = pa.decimal128(38, ESCALA)


def _f(nombre: str, tipo: pa.DataType, nulable: bool = True) -> pa.Field:
    return pa.field(nombre, tipo, nullable=nulable)


_I, _S, _D = pa.int64(), pa.string(), pa.date32()

TABLAS: dict[str, pa.Schema] = {
    "dim_proveedor": pa.schema(
        [_f("proveedor_key", _I, False), _f("proveedor_id_fiscal", _S), _f("proveedor_nombre", _S)]
    ),
    "dim_item": pa.schema([_f("item_key", _I, False), _f("codigo", _S), _f("descripcion", _S)]),
    "dim_fecha": pa.schema(
        [
            _f("fecha_key", _I, False),
            _f("fecha", _D, False),
            _f("anio", _I, False),
            _f("trimestre", _I, False),
            _f("mes", _I, False),
            _f("dia", _I, False),
        ]
    ),
    "fact_factura": pa.schema(
        [
            _f("numero_factura", _S),
            _f("cufe", _S),
            _f("tipo_documento", _S, False),
            _f("signo", _I, False),
            _f("proveedor_key", _I, False),
            _f("cliente_id_fiscal", _S),
            _f("cliente_nombre", _S),
            _f("fecha_emision_key", _I),
            _f("fecha_vencimiento_key", _I),
            _f("moneda", _S),
            _f("orden_compra", _S),
            _f("subtotal", _DINERO),
            _f("impuesto_total", _DINERO),
            _f("total", _DINERO),
            _f("pagadero", _DINERO),
            _f("archivo", _S, False),
            _f("forma_pago", _S),
            _f("medio_pago_codigo", _S),
            _f("cuadra", pa.bool_()),
        ]
    ),
    "fact_factura_linea": pa.schema(
        [
            _f("numero_factura", _S),
            _f("tipo_documento", _S, False),
            _f("signo", _I, False),
            _f("linea_numero", _I, False),
            _f("proveedor_key", _I, False),
            _f("item_key", _I, False),
            _f("fecha_emision_key", _I),
            _f("moneda", _S),
            _f("cantidad", _DINERO),
            _f("precio_unitario", _DINERO),
            _f("importe", _DINERO),
            _f("unidad", _S),
        ]
    ),
    "fact_factura_impuesto": pa.schema(
        [
            _f("numero_factura", _S),
            _f("tipo_documento", _S, False),
            _f("signo", _I, False),
            _f("proveedor_key", _I, False),
            _f("fecha_emision_key", _I),
            _f("moneda", _S),
            _f("tributo_codigo", _S),
            _f("tributo_nombre", _S),
            _f("porcentaje", _DINERO),
            _f("base", _DINERO),
            _f("impuesto", _DINERO),
        ]
    ),
}
"""Cada tabla y su esquema, en el orden de columnas del contrato."""

_SIGNO = {"factura": 1, "nota_credito": -1, "nota_debito": 1}

_EXTENSIONES = {".xml", ".zip"}


@dataclass(frozen=True)
class Rechazo:
    """Un archivo que no entro al modelo, y por que."""

    archivo: str
    motivo: str


@dataclass
class Modelo:
    """Las tablas listas para escribir, mas lo que quedo fuera."""

    tablas: dict[str, pa.Table]
    rechazados: list[Rechazo] = field(default_factory=list)
    leidos: int = 0
    """Archivos que se intentaron leer, entraran o no."""


def archivos(rutas: Iterable[Path]) -> list[Path]:
    """Los XML y ZIP a leer. Una carpeta se recorre entera, en orden de ruta.

    Un archivo nombrado explicitamente se lee aunque su extension no sea .xml o
    .zip: quien lo nombro sabe lo que es.
    """
    encontrados: list[Path] = []
    for ruta in rutas:
        ruta = Path(ruta)
        if ruta.is_dir():
            encontrados.extend(
                sorted(
                    (
                        p
                        for p in ruta.rglob("*")
                        if p.is_file() and p.suffix.lower() in _EXTENSIONES
                    ),
                    key=lambda p: p.as_posix(),
                )
            )
        else:
            encontrados.append(ruta)
    return encontrados


def _comprueba_escala(factura: Invoice) -> None:
    """Rechaza un importe con mas decimales de los que caben, en vez de redondearlo."""
    importes: list[Decimal | None] = [
        factura.subtotal,
        factura.impuesto_total,
        factura.total,
        factura.extras.get("ubl_payable_amount"),
    ]
    for linea in factura.lineas:
        importes += [linea.cantidad, linea.precio_unitario, linea.importe]
    for tributo in factura.extras.get("impuestos", []):
        importes += [tributo["porcentaje"], tributo["base"], tributo["impuesto"]]
    for valor in importes:
        if valor is None:
            continue
        exponente = valor.as_tuple().exponent
        if isinstance(exponente, int) and exponente < -ESCALA:
            raise ValueError(f"{valor} tiene mas de {ESCALA} decimales y no se redondea")


def _clave_proveedor(factura: Invoice) -> tuple[str, str]:
    if factura.proveedor_id_fiscal:
        return ("id", factura.proveedor_id_fiscal)
    return ("nombre", factura.proveedor_nombre or "")


def _clave_fecha(dia: date | None) -> int | None:
    return dia.year * 10000 + dia.month * 100 + dia.day if dia else None


def _orden(valor: str | None) -> tuple[bool, str]:
    """Para ordenar con None al final sin comparar None con str."""
    return (valor is None, valor or "")


def construir(rutas: Iterable[Path]) -> Modelo:
    """Lee cada archivo y arma las tablas del esquema estrella."""
    lista = archivos(rutas)
    rechazados: list[Rechazo] = []
    documentos: list[tuple[Path, Invoice]] = []
    vistos: dict[tuple[str, tuple[str, str], str], Path] = {}

    for ruta in lista:
        try:
            factura = leer(ruta)
            _comprueba_escala(factura)
            if factura.tipo_documento is None:
                raise ValueError("el documento no declara tipo_documento")
        except Exception as error:  # un archivo malo no frena a los demas
            rechazados.append(Rechazo(str(ruta), f"{type(error).__name__}: {error}"))
            continue

        if factura.numero_factura is not None:
            clave = (factura.tipo_documento, _clave_proveedor(factura), factura.numero_factura)
            if clave in vistos:
                rechazados.append(Rechazo(str(ruta), f"duplicado de {vistos[clave]}"))
                continue
            vistos[clave] = ruta
        documentos.append((ruta, factura))

    return Modelo(tablas=_tablas(documentos), rechazados=rechazados, leidos=len(lista))


def _tablas(documentos: list[tuple[Path, Invoice]]) -> dict[str, pa.Table]:
    # Proveedores: el nombre que se guarda es el del primer documento leido.
    proveedores: dict[tuple[str, str], Invoice] = {}
    items: set[tuple[str | None, str | None]] = set()
    dias: set[date] = set()
    for _, f in documentos:
        proveedores.setdefault(_clave_proveedor(f), f)
        items.update((linea.codigo, linea.descripcion) for linea in f.lineas)
        dias.update(d for d in (f.fecha_emision, f.fecha_vencimiento) if d is not None)

    clave_proveedor = {k: i for i, k in enumerate(sorted(proveedores), start=1)}
    clave_item = {
        k: i
        for i, k in enumerate(sorted(items, key=lambda k: (_orden(k[0]), _orden(k[1]))), start=1)
    }

    filas: dict[str, list[dict[str, Any]]] = {nombre: [] for nombre in TABLAS}
    for natural, clave in clave_proveedor.items():
        f = proveedores[natural]
        filas["dim_proveedor"].append(
            {
                "proveedor_key": clave,
                "proveedor_id_fiscal": f.proveedor_id_fiscal,
                "proveedor_nombre": f.proveedor_nombre,
            }
        )
    for (codigo, descripcion), clave in clave_item.items():
        filas["dim_item"].append({"item_key": clave, "codigo": codigo, "descripcion": descripcion})
    filas["dim_fecha"] = _calendario(dias)

    for ruta, f in documentos:
        assert f.tipo_documento is not None  # comprobado al leer
        comun = {
            "numero_factura": f.numero_factura,
            "tipo_documento": f.tipo_documento,
            "signo": _SIGNO[f.tipo_documento],
        }
        proveedor = clave_proveedor[_clave_proveedor(f)]
        emision = _clave_fecha(f.fecha_emision)
        filas["fact_factura"].append(
            comun
            | {
                "cufe": f.cufe,
                "proveedor_key": proveedor,
                "cliente_id_fiscal": f.cliente_id_fiscal,
                "cliente_nombre": f.cliente_nombre,
                "fecha_emision_key": emision,
                "fecha_vencimiento_key": _clave_fecha(f.fecha_vencimiento),
                "moneda": f.moneda,
                "orden_compra": f.orden_compra,
                "subtotal": f.subtotal,
                "impuesto_total": f.impuesto_total,
                "total": f.total,
                "pagadero": f.extras.get("ubl_payable_amount"),
                "archivo": str(ruta),
                "forma_pago": f.forma_pago,
                "medio_pago_codigo": f.medio_pago_codigo,
                "cuadra": _cuadra(f),
            }
        )
        for tributo in _por_tributo(f):
            filas["fact_factura_impuesto"].append(
                comun
                | {"proveedor_key": proveedor, "fecha_emision_key": emision, "moneda": f.moneda}
                | tributo
            )
        for numero, linea in enumerate(f.lineas, start=1):
            filas["fact_factura_linea"].append(
                comun
                | {
                    "linea_numero": numero,
                    "proveedor_key": proveedor,
                    "item_key": clave_item[(linea.codigo, linea.descripcion)],
                    "fecha_emision_key": emision,
                    "moneda": f.moneda,
                    "cantidad": linea.cantidad,
                    "precio_unitario": linea.precio_unitario,
                    "importe": linea.importe,
                    "unidad": linea.extras.get("unidad"),
                }
            )

    return {
        nombre: pa.Table.from_pylist(filas[nombre], schema=esquema)
        for nombre, esquema in TABLAS.items()
    }


def _cuadra(factura: Invoice) -> bool | None:
    """Si el total cumple la identidad del estandar (ver `factura-v1.md`).

    None cuando falta alguno de los tres importes: no hay nada que comprobar, y
    decir que cuadra seria afirmar algo que nadie verifico.
    """
    if factura.subtotal is None or factura.impuesto_total is None or factura.total is None:
        return None
    return not any(p.campo == "total" for p in factura.problemas())


def _suma(valores: list[Decimal | None]) -> Decimal | None:
    """None si falta cualquiera: una suma de solo los presentes pareceria completa."""
    if any(v is None for v in valores):
        return None
    return sum((v for v in valores if v is not None), Decimal(0))


def _por_tributo(factura: Invoice) -> list[dict[str, Any]]:
    """Una fila por tributo y tarifa: los TaxSubtotal iguales se suman."""
    grupos: dict[tuple[str | None, Decimal | None], list[dict[str, Any]]] = {}
    for tributo in factura.extras.get("impuestos", []):
        grupos.setdefault((tributo["codigo"], tributo["porcentaje"]), []).append(tributo)
    return [
        {
            "tributo_codigo": codigo,
            "tributo_nombre": next((t["nombre"] for t in grupo if t["nombre"]), None),
            "porcentaje": porcentaje,
            "base": _suma([t["base"] for t in grupo]),
            "impuesto": _suma([t["impuesto"] for t in grupo]),
        }
        for (codigo, porcentaje), grupo in grupos.items()
    ]


def _calendario(dias: set[date]) -> list[dict[str, Any]]:
    """Anios completos y contiguos: lo que Power BI exige a una tabla de fechas."""
    if not dias:
        return []
    dia = date(min(dias).year, 1, 1)
    fin = date(max(dias).year, 12, 31)
    filas: list[dict[str, Any]] = []
    while dia <= fin:
        filas.append(
            {
                "fecha_key": _clave_fecha(dia),
                "fecha": dia,
                "anio": dia.year,
                "trimestre": (dia.month - 1) // 3 + 1,
                "mes": dia.month,
                "dia": dia.day,
            }
        )
        dia += timedelta(days=1)
    return filas


def escribir(modelo: Modelo, salida: Path, formato: str = "parquet") -> list[Path]:
    """Escribe cada tabla y `rechazados.csv` en `salida`. Devuelve lo escrito."""
    if formato not in ("parquet", "csv"):
        raise ValueError(f"formato desconocido: {formato!r}")
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    escritos: list[Path] = []
    for nombre, tabla in modelo.tablas.items():
        destino = salida / f"{nombre}.{formato}"
        if formato == "parquet":
            pq.write_table(tabla, destino)
        else:
            pacsv.write_csv(tabla, destino)
        escritos.append(destino)

    # Siempre se escribe, aunque este vacio: su ausencia no debe leerse como "todo bien".
    rechazos = salida / "rechazados.csv"
    with rechazos.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(["archivo", "motivo"])
        escritor.writerows((r.archivo, r.motivo) for r in modelo.rechazados)
    escritos.append(rechazos)
    return escritos
