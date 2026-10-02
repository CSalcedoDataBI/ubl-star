"""El plugin de Claude Code no se desincroniza del paquete.

La skill fija la CLI a un tag (`@vX.Y.Z`). Si alguien sube la version del
paquete y olvida el plugin, o al reves, la skill llamaria a otra version de la
que describe. Estos tests lo impiden; el tag lo crea `release.yml` al mergear.
"""

import json
import re
import subprocess
import tomllib
from pathlib import Path

import yaml

import ubl_star

RAIZ = Path(__file__).resolve().parents[1]
MANIFIESTO = RAIZ / ".claude-plugin" / "plugin.json"
SKILL = RAIZ / "skills" / "leer-facturas-ubl" / "SKILL.md"


def _version_paquete() -> str:
    with (RAIZ / "pyproject.toml").open("rb") as f:
        version: str = tomllib.load(f)["project"]["version"]
    return version


def test_el_manifiesto_tiene_la_version_del_paquete() -> None:
    manifiesto = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
    assert manifiesto["name"] == "ubl-star"
    assert manifiesto["version"] == _version_paquete() == ubl_star.__version__


def _textos_de_la_skill() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in SKILL.parent.rglob("*.md"))


def test_la_skill_fija_la_cli_a_la_version_del_paquete() -> None:
    """Tanto el lanzador (`ubl-star@vX`) como los enlaces al contrato (`blob/vX`)."""
    texto = _textos_de_la_skill()
    fijadas = set(re.findall(r"ubl-star(?:@|/blob/)v(\d+\.\d+\.\d+)", texto))
    assert fijadas == {_version_paquete()}, f"versiones fijadas en la skill: {fijadas}"


def test_el_frontmatter_de_la_skill_es_yaml_valido() -> None:
    """Un `: ` suelto en la descripcion rompe el YAML para un parser estricto."""
    _, frontmatter, _ = SKILL.read_text(encoding="utf-8").split("---", 2)
    meta = yaml.safe_load(frontmatter)
    assert meta["name"] == "leer-facturas-ubl" == SKILL.parent.name
    assert 50 < len(meta["description"]) <= 1024


def test_la_skill_nunca_apunta_a_una_rama() -> None:
    """Un `@main` o un git+https sin version haria que el plugin cambie sin aviso."""
    texto = _textos_de_la_skill()
    for url in re.findall(r"github\.com/CSalcedoDataBI/ubl-star\S*", texto):
        assert re.search(r"(@|/blob/)v\d+\.\d+\.\d+", url), url


def test_el_manifiesto_lleva_lo_que_pide_el_directorio() -> None:
    manifiesto = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
    for campo in (
        "name",
        "displayName",
        "description",
        "version",
        "license",
        "homepage",
        "repository",
    ):
        assert manifiesto.get(campo), campo
    assert (RAIZ / "LICENSE").is_file()


def test_ningun_archivo_del_plugin_pasa_de_256_kib() -> None:
    """Por encima, el directorio de Anthropic retiene el envio para revision manual.

    El plugin es el repo entero (se instala todo), asi que se mira cada archivo
    rastreado por git, no solo `.claude-plugin/` y `skills/`.
    """
    rastreados = (
        subprocess.run(["git", "ls-files", "-z"], cwd=RAIZ, capture_output=True, check=True)
        .stdout.decode("utf-8")
        .split("\x00")
    )
    grandes = [
        nombre
        for nombre in rastreados
        if nombre and (RAIZ / nombre).is_file() and (RAIZ / nombre).stat().st_size >= 256 * 1024
    ]
    assert grandes == []
