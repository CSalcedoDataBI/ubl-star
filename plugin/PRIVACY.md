# Política de privacidad — ubl-star

*Vigente desde el 2026-10-02. Responsable: Cristobal Salcedo — contacto@csalcedodatabi.com*

Esta política cubre el **plugin ubl-star** para Claude y la herramienta de línea de comandos que ese
plugin ejecuta. El sitio [csalcedodatabi.com](https://csalcedodatabi.com/) tiene su propia política.

> **In short (English):** the plugin collects nothing and has no server. It runs the `ubl-star`
> command-line tool on your machine, pinned to an exact version; the first run downloads that
> version from GitHub and its Python dependencies from PyPI. Parsing is local and makes no network
> calls. What Claude reads from the output enters your conversation, so the plugin hands back files
> and totals rather than invoice rows.

## Qué recoge el plugin

**Nada.** El plugin es una skill (`leer-facturas-ubl`) y una página de referencia. No trae hooks, ni
servidor MCP, ni telemetría, ni analítica, ni procesos en segundo plano. No tiene servidor propio, así
que nada de lo que hagas con él llega al responsable.

## Qué ejecuta, lee y envía

| Cuándo | Qué pasa | A dónde va |
|---|---|---|
| Se activa la skill | Claude lee el texto de la skill desde la carpeta del plugin instalado | A ningún sitio: lectura local |
| Primera ejecución de una versión | `uv` (o `pip`) descarga `ubl-star` en la versión fijada `vX.Y.Z` | `github.com` (el repositorio público, solo lectura) |
| Primera ejecución de una versión | Se descargan las dependencias de Python (`pydantic`, `defusedxml`, `pyarrow` y las suyas) | `pypi.org` y `files.pythonhosted.org` (solo lectura) |
| Cada conversión | `ubl-star model` lee tus XML o ZIP y escribe tablas Parquet o CSV en la carpeta que indiques | A ningún sitio: el parseo es local y no hace llamadas de red |
| Cada respuesta | Claude lee los conteos de la CLI y, si se lo pides, totales calculados sobre las tablas | A tu conversación con Claude |

**Tus facturas no salen de tu máquina por el plugin.** La CLI no envía nada a ningún servicio: el
código no abre conexiones de red ni lee variables de entorno. Lo único que puede salir es lo que Claude
lee para responderte, y eso entra en tu conversación, que se rige por las condiciones de tu cuenta de
Claude. Por eso la CLI solo imprime conteos y la skill entrega archivos y agregados, no filas con
nombres, NIT o cédulas, salvo que tú pidas un documento concreto.

Los scripts de mantenimiento de este repositorio (los evals de `evals/` y los workflows de GitHub
Actions) **no** los ejecuta el plugin: solo corren cuando el responsable los lanza.

## Menores

El plugin es una herramienta para profesionales y no está dirigido a menores de 18 años.

## Cambios y contacto

Los cambios de esta política se hacen en este archivo y quedan en el historial del repositorio.
Preguntas: contacto@csalcedodatabi.com.
