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


EVALS = RAIZ / "evals"


def test_los_scaffolds_de_los_evals_son_identicos() -> None:
    """Uno solo de verdad, copiado en cada caso (el eval no deja salir del caso)."""
    scaffolds = sorted(EVALS.glob("*/scaffold.sh"))
    assert scaffolds, "no hay scaffolds"
    contenidos = {p.read_text(encoding="utf-8") for p in scaffolds}
    assert len(contenidos) == 1, [str(p) for p in scaffolds]


def test_el_scaffold_lee_la_version_y_no_la_escribe() -> None:
    """La version sale de pyproject (tolerando CRLF), nunca escrita a mano."""
    texto = next(EVALS.glob("*/scaffold.sh")).read_text(encoding="utf-8")
    assert "pyproject.toml" in texto and "tr -d '\\r'" in texto
    assert not re.search(r"@v\d+\.\d+\.\d+", texto), "version escrita a mano"
    # La cache, en la config de usuario y con ruta absoluta: el agente puede hacer
    # `cd $TMPDIR` antes de uvx y no ve la ~/.cache del scaffold (corrida real).
    assert '"$HOME/.config/uv/uv.toml"' in texto
    assert "> uv.toml" not in texto
    assert 'uvx --from "$origen" python' in texto  # el entorno del paso 3 de la skill


def test_los_evals_abren_la_red_solo_a_github_y_pypi() -> None:
    """Sin red, uv no resuelve el tag de git (probado con uv 0.12): el comando
    documentado y el workflow abren solo GitHub y PyPI."""
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    flujo = (RAIZ / ".github" / "workflows" / "evals.yml").read_text(encoding="utf-8")
    for dominio in ("github.com", "pypi.org", "files.pythonhosted.org"):
        assert f"WebFetch(domain:{dominio})" in readme, dominio
        assert f"WebFetch(domain:{dominio})" in flujo, dominio


def test_la_skill_usa_un_solo_entorno_fijado() -> None:
    """`uv run --with git+...` vuelve a pedir el git y no funciona sin red."""
    texto = _textos_de_la_skill()
    assert "uv run" not in texto
    assert "ubl-star@v" in texto and "python script.py" in texto


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
