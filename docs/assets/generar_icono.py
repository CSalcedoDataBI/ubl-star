"""Genera el icono del plugin: plugin/.claude-plugin/icon.png (1024 x 1024).

Un esquema estrella dibujado como estrella: el nodo central es la tabla de
hechos y los cinco de alrededor, las dimensiones. Paleta del banner del repo.
Sin texto a proposito: en el directorio el icono se ve a unos 64 px, y el autor
y la web ya salen en la ficha.

    python docs/assets/generar_icono.py

Requiere Pillow, que no es dependencia del paquete: se usa solo para esto.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

LADO = 1024
SUPERMUESTREO = 4  # se dibuja a 4x y se reduce, para bordes limpios
FONDO, MENTA, VERDE, CLARO = (15, 27, 24), (114, 235, 196), (17, 107, 98), (228, 240, 236)
DESTINO = Path(__file__).resolve().parents[2] / "plugin" / ".claude-plugin" / "icon.png"


def dibujar() -> Image.Image:
    w = LADO * SUPERMUESTREO
    img = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, w - 1], radius=int(w * 0.22), fill=FONDO)
    c, radio = w / 2, w * 0.29  # deja ~15 % de margen para mascaras redondas
    puntas = [
        (c + radio * math.cos(math.radians(-90 + 72 * i)), c + radio * math.sin(math.radians(-90 + 72 * i)))
        for i in range(5)
    ]
    for x, y in puntas:  # relaciones: hechos -> dimension
        d.line([(c, c), (x, y)], fill=VERDE, width=int(w * 0.045))
    for x, y in puntas:  # dimensiones
        r = w * 0.085
        d.ellipse([x - r, y - r, x + r, y + r], fill=MENTA)
    r = w * 0.15  # tabla de hechos
    d.ellipse([c - r, c - r, c + r, c + r], fill=CLARO)
    r = w * 0.095
    d.ellipse([c - r, c - r, c + r, c + r], fill=VERDE)
    return img.resize((LADO, LADO), Image.LANCZOS)


if __name__ == "__main__":
    dibujar().save(DESTINO, optimize=True)
    print(f"escrito {DESTINO}")
