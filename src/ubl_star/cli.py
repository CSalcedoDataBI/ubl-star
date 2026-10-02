"""`ubl-star model <xml|zip|carpeta>... --salida DIR` -> esquema estrella.

Codigos de salida: 0 todo leido, 1 hubo rechazados (las tablas se escriben igual
con lo que si entro), 2 error de uso (una ruta que no existe, ningun documento).

Por la salida estandar solo salen conteos. Lo que imprime esta CLI puede acabar
en una conversacion con un modelo; nombres, NIT, importes y nombres de archivo
(que en la DIAN suelen llevar el NIT del emisor) se quedan en los archivos.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ubl_star import __version__
from ubl_star.modelo import archivos, construir, escribir


def _parser() -> argparse.ArgumentParser:
    raiz = argparse.ArgumentParser(
        prog="ubl-star",
        description="De factura electronica UBL 2.1 a un esquema estrella listo para analizar.",
    )
    raiz.add_argument("--version", action="version", version=f"ubl-star {__version__}")
    sub = raiz.add_subparsers(dest="comando", required=True)

    model = sub.add_parser(
        "model",
        help="lee XML/ZIP (o carpetas) y escribe dim_* y fact_* en Parquet o CSV",
    )
    model.add_argument("rutas", nargs="+", type=Path, help="archivos .xml/.zip o carpetas")
    model.add_argument("--salida", "-o", type=Path, required=True, help="carpeta de salida")
    model.add_argument("--formato", choices=("parquet", "csv"), default="parquet")
    return raiz


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    faltan = [r for r in args.rutas if not r.exists()]
    if faltan:
        print(f"ubl-star: no existe: {', '.join(map(str, faltan))}", file=sys.stderr)
        return 2
    if not archivos(args.rutas):
        print("ubl-star: ningun XML ni ZIP en las rutas dadas", file=sys.stderr)
        return 2

    modelo = construir(args.rutas)
    escribir(modelo, args.salida, args.formato)

    documentos = modelo.tablas["fact_factura"].num_rows
    lineas = modelo.tablas["fact_factura_linea"].num_rows
    rechazados = len(modelo.rechazados)
    print(
        f"ubl-star model: {documentos} documentos, {lineas} lineas, "
        f"{rechazados} rechazados -> {args.salida}"
    )
    if rechazados:
        print(f"  revisa {args.salida / 'rechazados.csv'}")
        return 1
    return 0
