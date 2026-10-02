#!/bin/sh
# Prepara el espacio de trabajo de un eval.
#
# 1. ./buzon con las fixtures SINTETICAS del repo (nunca una factura real). La
#    factura DIAN va dentro de un ZIP, como llega del proveedor.
# 2. Una cache de uv con la CLI fijada ya descargada, para que la corrida no
#    dependa de la velocidad de PyPI. La red del agente se abre solo a GitHub y
#    PyPI desde la linea de comando del eval (ver README, seccion Evals): uv
#    siempre consulta GitHub para resolver un tag de git, asi que un modo offline
#    no sirve (probado con uv 0.12).
set -e
raiz=$(cd "$(dirname "$0")/../.." && pwd)
# `tr -d '\r'`: en un checkout de Windows pyproject.toml tiene CRLF y el `"$` del
# patron no casaria; la version saldria vacia y se pediria el tag `v`.
version=$(tr -d '\r' < "$raiz/pyproject.toml" | sed -n 's/^version = "\(.*\)"$/\1/p')
if [ -z "$version" ]; then
  echo "scaffold: no se pudo leer la version de pyproject.toml" >&2
  exit 1
fi
origen="git+https://github.com/CSalcedoDataBI/ubl-star@v$version"

mkdir -p buzon
# Buzon fijo (el mismo de tests/test_estrella.py): las cifras de los graders
# cuentan exactamente estos cinco documentos.
for f in dian_spd_601 dian_nota_credito dian_nota_debito peppol_invoice peppol_credit_note; do
  cp "$raiz/tests/fixtures/$f.xml" buzon/
done
python3 -m zipfile -c buzon/ad_dian_spd.zip buzon/dian_spd_601.xml
rm buzon/dian_spd_601.xml

# La cache va DENTRO de la carpeta del caso y se declara en la config de usuario
# de uv: el sandbox del agente no ve la ~/.cache que llena este script, y el
# agente puede hacer `cd $TMPDIR` antes de uvx (visto en corridas reales).
cache="$(pwd)/.uv-cache"
mkdir -p "$HOME/.config/uv"
printf 'cache-dir = "%s"\n' "$cache" > "$HOME/.config/uv/uv.toml"
uvx --from "$origen" ubl-star --version
uvx --from "$origen" python -c "import pyarrow"
ls buzon
