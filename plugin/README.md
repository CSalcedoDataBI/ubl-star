# ubl-star — plugin de Claude Code

Convierte facturas electrónicas **UBL 2.1** —el XML o el ZIP que envía la DIAN (Colombia) y las
facturas **PEPPOL / EN 16931** (Europa)— en un esquema estrella en Parquet o CSV, listo para Power BI.
Lee el XML, que es el documento legal: precisión total, sin OCR y sin modelo.

Una sola skill, `leer-facturas-ubl`. Le dices a Claude «convierte estas facturas de la DIAN en tablas
para Power BI» o «¿cuánto IVA hay en esta carpeta, restando las notas crédito?», y Claude llama a la
CLI de `ubl-star` fijada a una versión exacta, en vez de escribir un parser propio.

```text
/plugin marketplace add CSalcedoDataBI/ubl-star
/plugin install ubl-star@ubl-star
```

Requisitos: [`uv`](https://docs.astral.sh/uv/) (o `pip`), `git` y Python ≥ 3.11.

## Qué ejecuta, qué envía y qué descarga (what it runs, sends and fetches)

| Cuándo | Qué pasa | A dónde va |
|---|---|---|
| Se activa la skill | Claude lee el texto de la skill desde la carpeta del plugin | A ningún sitio: lectura local |
| Primera ejecución de una versión | `uv` descarga `ubl-star` en la versión fijada `vX.Y.Z` | `github.com`, solo lectura |
| Primera ejecución de una versión | Se descargan las dependencias de Python | `pypi.org` y `files.pythonhosted.org`, solo lectura |
| Cada conversión | La CLI lee tus XML o ZIP y escribe tablas en la carpeta que indiques | A ningún sitio: el parseo es local y no hace llamadas de red |
| Cada respuesta | Claude lee los conteos y los totales que calcula | A tu conversación con Claude |

El plugin no trae hooks, ni servidor MCP, ni telemetría, y no tiene servidor propio. La CLI solo
imprime conteos, y la skill entrega archivos y totales en vez de volcar filas con nombres, NIT o
cédulas. Los evals de `evals/` son herramientas del mantenedor: el plugin no los ejecuta.

Política de privacidad: [PRIVACY.md](PRIVACY.md). Código, contrato de salida y documentación
completa: [github.com/CSalcedoDataBI/ubl-star](https://github.com/CSalcedoDataBI/ubl-star).
Licencia MIT.
