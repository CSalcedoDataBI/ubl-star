"""La entrada real: lo que llega es un ZIP, no un XML suelto.

La DIAN entrega el adjunto como un ZIP con el XML firmado y su representacion
grafica en PDF. Este modulo hace una sola cosa: devolver el texto del XML de la
factura. Si hay mas de uno, no elige — elegir seria inventar.
"""

import zipfile
from pathlib import Path


class SinFacturaEnAdjunto(Exception):
    """El adjunto no trae ningun XML."""


class AdjuntoAmbiguo(Exception):
    """El adjunto trae mas de un XML y ninguna regla dice cual es la factura."""


def localizar_xml(ruta: Path) -> str:
    """Devuelve el texto del XML de la factura, venga suelto o dentro del ZIP."""
    ruta = Path(ruta)

    if ruta.suffix.lower() == ".xml":
        return ruta.read_text(encoding="utf-8")

    with zipfile.ZipFile(ruta) as adjunto:
        candidatos = [
            nombre
            for nombre in adjunto.namelist()
            if nombre.lower().endswith(".xml") and not nombre.endswith("/")
        ]

        if not candidatos:
            raise SinFacturaEnAdjunto(f"{ruta.name} no contiene ningun XML")
        if len(candidatos) > 1:
            raise AdjuntoAmbiguo(
                f"{ruta.name} contiene {len(candidatos)} XML y ninguna regla dice "
                f"cual es la factura: {', '.join(sorted(candidatos))}"
            )

        return adjunto.read(candidatos[0]).decode("utf-8")
