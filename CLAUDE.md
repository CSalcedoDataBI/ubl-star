# ubl-star

Lector de facturas electrónicas UBL 2.1 (adjuntos de la DIAN) y plugin de Claude Code que lo envuelve.
El norte del repo —qué es, para quién, qué no hace— está en [FICHA.md](FICHA.md): léelo antes de
proponer cambios de alcance.

## Reglas que no se negocian

- **Ninguna factura real** en el repo, en issues ni en PRs. Las fixtures son sintéticas y salen de
  `tests/fixtures/generar.py`. Detalle en [CONTRIBUTING.md](CONTRIBUTING.md).
- **Cero inferencia:** un campo que no está en el XML se reporta ausente, nunca se adivina.
- **Dinero en `Decimal`**; el contrato rechaza `float`.
- Código y docstrings en español; commits en inglés (conventional commits).
- El repo es público: nada de rutas locales ni enlaces a recursos privados en archivos versionados.

## Checks antes de abrir un PR

```bash
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src
python -m pytest -q --cov
```

## Plugin en el directorio de Anthropic

La carpeta publicada es `plugin/`. El directorio rastrea la rama `stable`, que solo avanza con un
release: no la muevas a mano. `main` es libre; agrupa los cambios y no fusiones un PR de release mientras
haya una versión en revisión.
