#!/bin/sh
# Prepara ./buzon en el espacio de trabajo del eval con las fixtures SINTETICAS
# del repo: nunca una factura real. La factura DIAN va dentro de un ZIP, como
# llega del proveedor, para que el eval ejercite tambien la lectura del adjunto.
set -e
raiz=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p buzon
cp "$raiz"/tests/fixtures/*.xml buzon/
python3 -m zipfile -c buzon/ad_dian_spd.zip buzon/dian_spd_601.xml
rm buzon/dian_spd_601.xml
ls buzon
