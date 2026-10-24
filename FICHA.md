# Ficha — ubl-star

> Ficha de esta herramienta. La lee su experto (`.claude/agents/experto.md`) en cada PR.
> Se mantiene con las reglas del mantenedor. La aprueba el mantenedor (línea `Aprobada:`); cambiarla exige una nueva aprobación.

## Qué es

- **Qué construye y para quién:** Una librería y CLI en Python que lee el XML de facturas electrónicas UBL 2.1 (DIAN, PEPPOL / EN 16931), facturas, notas crédito y notas débito, y escribe un esquema estrella en Parquet o CSV listo para Power BI, con lectura exacta y sin OCR ni modelo. Incluye un plugin de Claude Code (`plugin/`) que hace que Claude use la CLI fijada en vez de escribir un parser propio. Es para analistas y usuarios de Power BI que reciben facturas electrónicas.
- **Papel:** tool
- **Gemelo público/privado:** tiene un gemelo privado

## Norte

- **Plan vigente:** [issue #36](https://github.com/CSalcedoDataBI/ubl-star/issues/36)
- **Lo que esta herramienta NO es:**
  - No lee PDF, escaneos ni fotos: sin OCR.
  - No infiere campos: lo que no está en el XML se reporta ausente.
  - No emite ni firma facturas.
  - No envía datos a ningún servicio: el parseo es local.
  - No es un paquete de PyPI (hoy se instala desde un tag de GitHub).

## Zonas protegidas

Lo que no se toca sin un paso del plan que lo nombre:

- `docs/contrato/factura-v1.md` y `docs/contrato/estrella-v1.md`: son el contrato de salida, anclado por tests. Quitar, renombrar o cambiar el tipo de un campo es v2.
- `.githooks/pre-commit` y el job `barrera anti-contaminacion`: son lo único que impide que entre una factura real a un repo público.
- `tests/fixtures/generar.py` y `tests/fixtures/golden/`: las fixtures son sintéticas y salen de código; un golden que cambia es un cambio de salida del parser.
- La versión en sus tres sitios (`pyproject.toml` con `src/ubl_star/__init__.py`, `plugin/.claude-plugin/plugin.json` y el pin `@vX.Y.Z` de la skill): `tests/test_plugin.py` exige que coincidan.
- `.github/workflows/release.yml` y la rama `stable`: crean tags inmutables y alimentan el directorio de plugins.
- `plugin/` (manifiesto, icono, skill, `PRIVACY.md`, `LICENSE`): es lo que se instala y lo que revisa el directorio.
- El job `CI completo` de `.github/workflows/ci.yml`: es el único check que exige el ruleset de `main`; renombrarlo deja las PR esperando un check que no llega.

## Capa y feedback

- **Capa de nodo:** etl
- **Skill de feedback:** ninguna

## Check y experto

- **Check de CI requerido:** `CI completo` (job agregador de `ci.yml`: depende de la matriz `test`, de `plugin de Claude Code` y de `barrera anti-contaminacion`, y falla si alguno falla o se cancela). Es el único que exige el ruleset de `main`.
- **Suite de pruebas:** `python -m pytest -q --cov` (cobertura mínima del 90 %), junto con `python -m ruff check src tests`, `python -m ruff format --check src tests` y `python -m mypy src`
- **Runner:** GitHub (repo público)
- **Formato de tag:** `vX.Y.Z`
- **Experto:** `.claude/agents/experto.md`
- **¿Plugin del directorio?:** sí: `stable` no se toca, y cada publicación sigue el protocolo de releases del directorio
- **Partes visibles que aprueba Cristóbal:** subir de versión (crea el tag y mueve `stable`, lo que abre una revisión en el directorio); `plugin/.claude-plugin/plugin.json` e `icon.png`; la descripción y el texto de `plugin/skills/leer-facturas-ubl/SKILL.md`; `plugin/README.md`; `README.md`; `PRIVACY.md`.

## Aprobación

Aprobada: 2026-10-24 (mantenedor)
