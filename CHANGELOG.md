# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); las versiones siguen
[SemVer](https://semver.org/lang/es/). Cada versión tiene su tag `vX.Y.Z`, que es el que fija el
plugin de Claude Code.

## [Sin publicar]

### Cambiado

- Evals del plugin: el sandbox se abre solo a GitHub y PyPI, y la suite saca 1.00 en los cuatro casos
  con el plugin (Δ medio +0.58 frente a no tenerlo) ([#24]).
- Documentación: `CONTRIBUTING.md` y `CHANGELOG.md` propios; el README queda orientado a quien usa la
  herramienta.

## [0.2.3] — 2026-10-02

### Corregido

- La skill agrega cifras con `uvx --from git+…@vX python`, el mismo entorno fijado que la CLI. El
  comando anterior (`uv run --with`) volvía a pedir el git ([#23]).
- Los evals ya pueden correr: scaffold que lee la versión de `pyproject.toml`, buzón fijo de cinco
  documentos y workflow manual en GitHub Actions ([#23]).

## [0.2.2] — 2026-10-02

### Corregido

- `cuadra()` daba un falso descuadre en facturas PEPPOL con descuento o cargo de documento: en EN 16931
  el total con impuestos ya los descuenta. Ahora se acepta la identidad DIAN o la de EN 16931 ([#21],
  [#22]).

### Añadido

- Contrato `factura-v1`: campos opcionales `descuento_total` y `cargo_total` (no rompe v1).

## [0.2.1] — 2026-10-02

### Añadido

- **Plugin de Claude Code** con una skill, `leer-facturas-ubl`: Claude llama a la CLI fijada a una
  versión exacta en vez de escribir un parser propio. Incluye marketplace propio, evals y validación
  estricta en CI ([#13], [#20]).
- `release.yml` crea el tag de versión al mergear a `main`.

## [0.2.0] — 2026-10-02

### Añadido

- **CLI `ubl-star model`**: de XML, ZIP o carpetas a un esquema estrella (`dim_proveedor`, `dim_item`,
  `dim_fecha`, `fact_factura`, `fact_factura_linea`) en Parquet o CSV, más `rechazados.csv`. Contrato
  `estrella-v1` ([#6], [#19]).
- Notas crédito y débito (`CreditNote`, `DebitNote`), con el campo `tipo_documento` y la factura
  corregida en `extras` ([#11], [#16]).
- Perfil **PEPPOL BIS 3.0 / EN 16931**: vencimiento en `cbc:DueDate`, IVA en `PartyTaxScheme`, artículo
  en `cbc:Name`, código del vendedor y orden de compra ([#5], [#18]).
- Fixtures sintéticas DIAN y PEPPOL con golden files ([#5], [#18]).

### Corregido

- `desanidar` reconoce el documento por el elemento, no por el texto: acepta el Invoice escapado sin
  CDATA y la raíz con prefijo ([#12], [#15]).

### Cambiado

- El CI exige formato (`ruff format`) y una cobertura mínima del 90 % ([#17]).

## [0.1.0] — 2026-08-13

### Añadido

- Lector UBL 2.1: localiza el XML dentro del ZIP del adjunto DIAN, desanida el Invoice del
  `AttachedDocument` y lo mapea al contrato `factura-v1` ([#2], [#3], [#4], [#8]).
- Barrera anti-contaminación (`.githooks/pre-commit`) y CI en Linux y Windows ([#7], [#10]).

[Sin publicar]: https://github.com/CSalcedoDataBI/ubl-star/compare/v0.2.3...HEAD
[0.2.3]: https://github.com/CSalcedoDataBI/ubl-star/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/CSalcedoDataBI/ubl-star/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/CSalcedoDataBI/ubl-star/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/CSalcedoDataBI/ubl-star/releases/tag/v0.2.0
[0.1.0]: https://github.com/CSalcedoDataBI/ubl-star/pull/8
[#2]: https://github.com/CSalcedoDataBI/ubl-star/issues/2
[#3]: https://github.com/CSalcedoDataBI/ubl-star/issues/3
[#4]: https://github.com/CSalcedoDataBI/ubl-star/issues/4
[#5]: https://github.com/CSalcedoDataBI/ubl-star/issues/5
[#6]: https://github.com/CSalcedoDataBI/ubl-star/issues/6
[#7]: https://github.com/CSalcedoDataBI/ubl-star/issues/7
[#8]: https://github.com/CSalcedoDataBI/ubl-star/pull/8
[#10]: https://github.com/CSalcedoDataBI/ubl-star/pull/10
[#11]: https://github.com/CSalcedoDataBI/ubl-star/issues/11
[#12]: https://github.com/CSalcedoDataBI/ubl-star/issues/12
[#13]: https://github.com/CSalcedoDataBI/ubl-star/issues/13
[#15]: https://github.com/CSalcedoDataBI/ubl-star/pull/15
[#16]: https://github.com/CSalcedoDataBI/ubl-star/pull/16
[#17]: https://github.com/CSalcedoDataBI/ubl-star/pull/17
[#18]: https://github.com/CSalcedoDataBI/ubl-star/pull/18
[#19]: https://github.com/CSalcedoDataBI/ubl-star/pull/19
[#20]: https://github.com/CSalcedoDataBI/ubl-star/pull/20
[#21]: https://github.com/CSalcedoDataBI/ubl-star/issues/21
[#22]: https://github.com/CSalcedoDataBI/ubl-star/pull/22
[#23]: https://github.com/CSalcedoDataBI/ubl-star/pull/23
[#24]: https://github.com/CSalcedoDataBI/ubl-star/pull/24
