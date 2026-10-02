#!/bin/sh
# Prepara el espacio de trabajo de un eval.
#
# 1. ./buzon con las fixtures SINTETICAS del repo (nunca una factura real). La
#    factura DIAN va dentro de un ZIP, como llega del proveedor.
# 2. La CLI fijada, ya descargada. El Bash del agente corre en un sandbox SIN red,
#    asi que `uvx --from git+...@vX.Y.Z` no podria descargar nada. Este script si
#    tiene red: llena una cache de uv local al caso y deja `uv.toml` en modo
#    offline. El comando de la skill, sin cambios, resuelve desde esa cache.
set -e
raiz=$(cd "$(dirname "$0")/../.." && pwd)
version=$(sed -n 's/^version = "\(.*\)"$/\1/p' "$raiz/pyproject.toml")
origen="git+https://github.com/CSalcedoDataBI/ubl-star@v$version"

mkdir -p buzon
# Buzon fijo (el mismo de tests/test_estrella.py): las cifras de los graders
# cuentan exactamente estos cinco documentos.
for f in dian_spd_601 dian_nota_credito dian_nota_debito peppol_invoice peppol_credit_note; do
  cp "$raiz/tests/fixtures/$f.xml" buzon/
done
python3 -m zipfile -c buzon/ad_dian_spd.zip buzon/dian_spd_601.xml
rm buzon/dian_spd_601.xml

printf 'cache-dir = ".uv-cache"\n' > uv.toml
uvx --from "$origen" ubl-star --version
uvx --from "$origen" python -c "import pyarrow"
printf 'cache-dir = ".uv-cache"\noffline = true\n' > uv.toml
ls buzon
