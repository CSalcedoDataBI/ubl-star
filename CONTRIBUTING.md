# Contribuir a ubl-star

Esta guía es la específica de este repositorio y, donde difiere, manda sobre la
[guía general de la cuenta](https://github.com/CSalcedoDataBI/.github/blob/main/CONTRIBUTING.md).
Lo de allí sigue valiendo: abre un issue antes de cualquier cosa que no sea una errata, y piensa que un
issue es público desde el primer segundo.

## La regla que no se negocia: ninguna factura real

Una factura DIAN lleva nombre, NIT, cédula, dirección, correo y CUFE de personas reales. Este repositorio
es **público**, y una fuga no se deshace: un `git rm` posterior no la saca del historial que ya se clonó.

- **No adjuntes facturas reales a un issue ni a un PR**, ni siquiera "tapando" datos. Si un XML falla,
  reprodúcelo con una fixture sintética (ver abajo) o describe la estructura, no los valores.
- Las fixtures son **sintéticas y se generan por código** en `tests/fixtures/generar.py`. Nadie las
  escribe a mano: así es evidente que cada NIT, nombre e importe salió de ese archivo.
- El hook `.githooks/pre-commit` bloquea cualquier XML, ZIP, PDF o imagen fuera de `tests/fixtures/`,
  con una sola excepción de ruta exacta: el icono del plugin, `plugin/.claude-plugin/icon.png`.
  Git no lo lee por su cuenta: hay que activarlo (siguiente sección).

## Preparar el entorno

```bash
git config core.hooksPath .githooks   # obligatorio: activa la barrera anti-contaminación
pip install -e ".[dev]"
```

Requiere Python ≥ 3.11.

## Los checks

Son exactamente los que corre el CI en cada PR, en Linux y Windows con Python 3.11 y 3.13. Si están en
rojo en local, lo estarán en el PR:

```bash
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src
python -m pytest -q --cov          # falla por debajo del 90 % de cobertura (con ramas)
```

El CI además valida el plugin con `claude plugin validate --strict` y comprueba que el hook sea
ejecutable y bloquee de verdad. `main` está protegida: solo entra por PR, con todos los checks en verde
y la rama al día, y se mergea con squash.

## Cómo se trabaja un cambio

1. **Primero un test que falle.** Para un bug, un test que lo reproduzca con una fixture sintética; para
   una función nueva, el test del comportamiento esperado. Tiene que fallar antes del arreglo.
2. **El arreglo mínimo** que lo pone en verde.
3. Los checks de arriba, en verde.

### Fixtures y golden files

Una fixture nueva se añade como función en `tests/fixtures/generar.py` y se registra en `FIXTURES`.
Cada una tiene su **golden file** en `tests/fixtures/golden/` con la salida completa del parser. Para
escribir las fixtures en disco y regenerar los golden:

```bash
python -m tests.fixtures.generar --golden
```

Un golden que cambia es un cambio en la salida del parser: el diff se revisa en el PR, no se acepta a
ciegas. `tests/test_fixtures.py` falla si un archivo no coincide con su generador o si sobra o falta
alguno.

### El contrato de salida

`docs/contrato/factura-v1.md` y `docs/contrato/estrella-v1.md` **son** el contrato, y cada uno tiene un
test que lo ancla al código. Un cambio de modelo se hace en el documento y en el código a la vez.
Añadir un campo opcional no rompe v1; quitar o renombrar un campo, o cambiarle el tipo, es v2.

## Versiones y release

La versión vive en tres sitios que deben coincidir, y `tests/test_plugin.py` falla si se separan:

- `pyproject.toml` (y `src/ubl_star/__init__.py`);
- `plugin/.claude-plugin/plugin.json`;
- el pin `@vX.Y.Z` en `plugin/skills/leer-facturas-ubl/` (el plugin llama a la CLI fijada a ese tag).

**Cualquier cambio del paquete o del plugin se anota en `CHANGELOG.md`**, bajo `[Sin publicar]`, y
sale con la siguiente versión. Mientras no se suba, la skill sigue fijada a la versión anterior y la
describe a ella: el PR que sube la versión es el que actualiza la skill. Al mergear a `main`,
`.github/workflows/release.yml` crea el tag `vX.Y.Z` si todavía no existe. Un tag publicado no se
mueve.

### Releases y el directorio de plugins

El directorio de plugins de claude.ai sigue la rama **`stable`**, no `main`. Revisa cada commit que
llega a la rama que sigue y lo pone en revisión, en lugar del anterior. `stable` solo avanza cuando
`release.yml` crea un tag de versión, así que `main` puede recibir commits a diario sin abrir una
revisión nueva cada vez.

- **Agrupa el trabajo.** Una versión es un ciclo de revisión que se mide en días, no un despliegue.
- **Prueba antes de subir la versión**, en Claude Code con el plugin local
  (`claude --plugin-dir plugin`). Lo que hay en claude.ai es siempre lo que el revisor aprobó.
- **No subas la versión mientras otra está en revisión**, salvo que lleve un arreglo de seguridad:
  la sustituiría.
- `stable` nunca se mueve a mano fuera de un release, y nunca se fuerza (un ruleset lo impide).
- Si el paso de `stable` falla tras crear el tag, **re-ejecuta la corrida** (Re-run jobs): encuentra el
  tag en ese mismo commit y vuelve a intentar el avance; si `stable` ya lo contiene, no hace nada.

## Evals del plugin

`plugin/evals/` mide si la skill se activa y si las respuestas son correctas, con y sin el plugin, sobre las
fixtures sintéticas:

```bash
claude plugin eval plugin --scaffold --trust-plugin --allow-tools Bash "WebFetch(domain:github.com)" "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)"
```

- `--allow-tools Bash` hace falta porque la skill ejecuta la CLI. Ese Bash corre en un sandbox **sin
  red**, y los tres `WebFetch(domain:…)` le abren solo GitHub (para resolver el tag fijado) y PyPI
  (para las dependencias). Un modo offline no sirve: `uv` siempre consulta GitHub para resolver un
  tag de git.
- **Linux / macOS:** el sandbox necesita `bubblewrap` y `socat` en Linux.
- **Windows:** no hay sandbox nativo para Bash. Córrelos dentro de una distro WSL2 con Linux de verdad
  (por ejemplo `wsl -d Ubuntu-24.04`), con `uv` y Claude Code instalados en esa distro. El caso
  `pdf-fuera-de-alcance` no usa Bash y sí corre en Windows sin `--allow-tools`.
- También hay un workflow manual, **Evals**, en GitHub Actions. Necesita el secreto
  `ANTHROPIC_API_KEY` en el repositorio.

Los evals no forman parte del CI de cada PR: gastan modelo y su veredicto solo cambia si cambia la
skill.

## Verificación manual del hook

Tras tocar `.githooks/pre-commit`, confirma **dos cosas distintas**: que git puede ejecutarlo y que hace
lo suyo. Fallan por separado, y comprobar lo segundo no detecta lo primero.

**1. Que está instalado y es ejecutable.** Git solo ejecuta hooks con el bit de ejecución. Si falta, en
Linux y macOS el hook se omite **en silencio**, sin error y con el commit aceptado:

```bash
git config core.hooksPath              # no debe salir vacío; apunta a .githooks
git ls-files -s .githooks/pre-commit   # el modo debe ser 100755, no 100644
```

Si sale `100644`, se arregla así:

```bash
git update-index --chmod=+x .githooks/pre-commit
```

**2. Que git lo dispara de verdad.** Un `git commit` real (no `sh`) sobre un caso que debe fallar. No
commitea nada, precisamente porque el hook lo rechaza:

```bash
touch factura-real.xml
git add -f factura-real.xml
git commit -m "prueba"      # BLOQUEADO + exit 1. Si el commit PASA, el hook no se está ejecutando.
git restore --staged factura-real.xml && rm factura-real.xml
```

**3. Que la lógica cubre cada caso.** Aquí sí conviene invocar el script directo. Los `-f` fuerzan el
paso del `.gitignore`, que es justo lo que el hook debe interceptar:

```bash
touch factura-real.xml factura.Xml
git add -f factura-real.xml && sh .githooks/pre-commit   # BLOQUEADO: XML fuera de fixtures
git reset
git add -f factura.Xml      && sh .githooks/pre-commit   # BLOQUEADO: la mayúscula mixta también cuenta
git reset
mkdir -p tests/fixtures && touch tests/fixtures/sintetica.xml
git add -f tests/fixtures/sintetica.xml && sh .githooks/pre-commit  # pasa: fixture sintética
git reset
rm factura-real.xml factura.Xml tests/fixtures/sintetica.xml
```

`factura.Xml` cubre una regresión real: el filtro comparaba extensiones literales (`*.xml|*.XML`), así
que `.Xml` entraba sin más. El paso 1 no sobra teniendo el 2: en Windows el bit de modo ni se consulta
y el paso 2 se ve idéntico con `100644` y con `100755`. `git ls-files` es la única comprobación que ve
el fallo desde cualquier plataforma, y es un fallo que ya ocurrió en otro proyecto: un hook estuvo meses
sin efecto en Linux y macOS sin que nada lo delatara.

## Seguridad

Un problema de seguridad no va en un issue público: sigue la
[política de seguridad](https://github.com/CSalcedoDataBI/.github/blob/main/SECURITY.md) (pestaña
**Security** → *Report a vulnerability*).
