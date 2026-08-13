# ubl-star

**De factura electrónica UBL 2.1 a hechos listos para analizar.**

Donde la factura electrónica es obligatoria, el documento legal **no es el PDF: es el XML**. El PDF
es su representación gráfica — una foto del original. Leer el XML no es una optimización, es leer la
fuente: **100% de precisión, cero OCR, cero tokens, cero modelo.**

`ubl-star` toma ese XML y entrega `dim_proveedor`, `dim_fecha`, `dim_item` y `fact_factura_linea` en
Parquet, listos para un Lakehouse.

> Estado: lee el ZIP del adjunto, localiza el XML y lo parsea al contrato de salida versionado.
> El modelo dimensional en Parquet es el siguiente paso.

## Por qué existe

Todo el esfuerzo de la industria está en leer el PDF: OCR, layout, modelos de visión, plantillas por
proveedor. Es trabajo real y difícil — pero en muchos países se está resolviendo un problema que ya
venía resuelto en el adjunto.

- **Colombia (DIAN)** — la factura se emite en XML UBL 2.1, firmada con certificado p12 y validada
  por los servicios web de la DIAN antes de llegar al receptor. El CUFE la identifica.
- **Europa (PEPPOL / EN 16931)** — el mismo UBL 2.1 como sintaxis de la factura electrónica
  transfronteriza.

Un solo parser cubre ambos. Lo que cambia entre jurisdicciones son las extensiones y los campos
fiscales, no la estructura del documento.

## Cómo funciona

1. **Entrada** — un XML UBL 2.1, o el ZIP del adjunto que lo contiene.
2. **Parseo** — sin adivinar: cada campo sale de su ruta en el estándar.
3. **Mapeo** — al contrato de factura canónico (emisor, receptor, líneas, impuestos, totales).
4. **Modelo** — esquema estrella → Parquet / CSV.

No hay escalón caro porque no hay ambigüedad que resolver. Si un campo no está en el XML, no está —
y eso se reporta, no se inventa.

## Alcance — y lo que queda fuera a propósito

`ubl-star` lee **XML**. Si lo que tienes es un PDF escaneado, una foto o un PDF sin adjunto, esta no
es tu herramienta: la lectura óptica es otro problema, con otro costo, otra tasa de error y otra
forma de auditarse. **Mezclar los dos caminos es lo que hace que un extractor de facturas no se pueda
verificar** — cuando un campo puede venir de una ruta exacta del estándar o de un modelo que lo
adivinó, ya no sabes cuál de las dos ocurrió.

Aquí solo pasa lo primero. Un campo que no está en el XML se reporta ausente.

## El contrato de salida

Las tablas, las columnas y las claves que produce `ubl-star` están declaradas en un **contrato
versionado**, y hay un test que ancla la salida a ese documento. La razón es que otra herramienta
—leyendo otra fuente— pueda entregar exactamente el mismo modelo y ser intercambiable aguas abajo,
sin compartir una línea de código con esta.

## Desarrollo

```bash
git config core.hooksPath .githooks   # obligatorio: barrera anti-contaminación
pip install -e ".[dev]"
pytest
```

El primer comando no es cosmético. Este repo es **público** y el hook es lo único que impide que una
factura real —con nombre, NIT, cédula, dirección y CUDE de personas de verdad— entre al historial.
**Git no lee `.githooks/` por su cuenta:** sin ese `git config`, el archivo está ahí y nadie lo
llama. Y en un repo público la fuga no se deshace — un `git rm` posterior no la saca del historial
que ya se clonó.

Las fixtures son sintéticas y se generan por código (`tests/fixtures/generar.py`). Es lo que permite
que el hook sea tajante: si un documento aparece fuera de `tests/fixtures/`, solo puede ser real.

### Verificación manual del hook

Tras tocar `.githooks/pre-commit`, confirma **dos cosas distintas**: que git puede ejecutarlo, y que
hace lo suyo. Fallan por separado, y comprobar lo segundo no detecta lo primero.

**1. Que está instalado y es ejecutable.** Git solo ejecuta hooks que llevan el bit de ejecución. Si
falta, en Linux y macOS el hook se omite **en silencio** — sin error, sin aviso, commit aceptado:

```bash
git config core.hooksPath              # no debe salir vacío; apunta a .githooks
git ls-files -s .githooks/pre-commit   # el modo debe ser 100755, no 100644
```

Si sale `100644`, el hook está muerto fuera de Windows y se revive así:

```bash
git update-index --chmod=+x .githooks/pre-commit
```

**2. Que git lo dispara de verdad.** Un `git commit` real —no `sh`— sobre un caso que debe fallar.
No commitea nada, precisamente porque el hook lo rechaza:

```bash
touch factura-real.xml
git add -f factura-real.xml
git commit -m "prueba"      # BLOQUEADO + exit 1. Si el commit PASA, el hook no se está ejecutando.
git restore --staged factura-real.xml && rm factura-real.xml
```

**3. Que la lógica cubre cada caso.** Aquí sí conviene invocar el script directo: es rápido y el
caso que *pasa* no acaba commiteando nada por error. Los `-f` fuerzan el paso del `.gitignore`, que
es justo lo que el hook debe interceptar:

```bash
touch factura-real.xml factura.Xml
git add -f factura-real.xml && sh .githooks/pre-commit   # BLOQUEADO: XML fuera de fixtures
git reset
git add -f factura.Xml      && sh .githooks/pre-commit   # BLOQUEADO: mayúscula mixta también cuenta
git reset
mkdir -p tests/fixtures && touch tests/fixtures/sintetica.xml
git add -f tests/fixtures/sintetica.xml && sh .githooks/pre-commit  # pasa: fixture sintética
git reset
rm factura-real.xml factura.Xml tests/fixtures/sintetica.xml
```

`factura.Xml` cubre una regresión concreta, y la mayúscula mixta es deliberada. El filtro comparaba
extensiones literales (`*.xml|*.XML`), así que `.xml` y `.XML` se bloqueaban pero **`.Xml` entraba
sin más**. Un `.ZIP` en mayúscula no sirve como caso de prueba: ese sí estaba en la lista. Lo que se
colaba era justo lo que ninguna de las dos variantes escritas contemplaba.

El paso 1 no sobra teniendo el 2: en Windows el bit de modo ni se consulta y los hooks corren igual,
así que el paso 2 se ve idéntico con `100644` y con `100755`. El `git ls-files` es la única
comprobación que ve el fallo desde cualquier plataforma — y es un fallo real, no hipotético: le pasó
a `pdfstar`, donde el hook estuvo meses sin efecto en Linux y macOS sin que nada lo delatara.

## Licencia

MIT. Solo dependencias permisivas (MIT / Apache-2.0 / BSD) — el mismo criterio que `pdfstar`.

---

© Cristobal Salcedo · [CSalcedoDataBI](https://csalcedodatabi.com/)
