# Lector UBL 2.1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir un ZIP de adjunto DIAN (o un XML UBL 2.1 suelto) en el contrato `Invoice`, con cada campo anclado a su ruta del estándar y sin inventar nada.

**Architecture:** Tres piezas con una frontera clara cada una. `zip.py` localiza el XML de la factura dentro del adjunto. `parser.py` desanida el `Invoice` que la DIAN embebe en CDATA dentro del `AttachedDocument` y lo mapea campo por campo al contrato. `schema/` declara ese contrato, y un test de conformidad lo ancla a un documento versionado para que la implementación hermana que lee PDF produzca lo mismo.

**Tech Stack:** Python ≥3.11, pydantic 2, defusedxml, pytest, ruff, mypy, hatchling. Layout `src/`, igual que `pdfstar`.

**Cierra las issues:** #4 (entrada ZIP), #3 (parser), #2 (contrato de salida).

## Global Constraints

- **Licencias:** solo permisivas (MIT / Apache-2.0 / BSD / PSF). Vetado todo AGPL/GPL. Mismo criterio que `pdfstar`.
- **Sin datos reales.** Ninguna factura, NIT, cédula, nombre, dirección, contrato, CUDE o serial de medidor real entra a este repo. Las fixtures son inventadas y se generan por código.
- **El dinero es `Decimal` y el contrato rechaza `float`.** Copiado de `pdfstar/src/pdfstar/schema/__init__.py`: `0.1 + 0.2 != 0.3` y un céntimo de deriva es un descuadre que alguien persigue.
- **Cero inferencia.** Un campo que no está en el XML se reporta ausente (`None`). Nunca se adivina, nunca se calcula un valor que el documento no trae.
- **Cada campo del contrato se prueba contra su ruta XPath del estándar**, no contra el valor de una fixture.
- `line-length = 100`, `target-version = "py311"` en ruff. Igual que `pdfstar`.
- Idioma: código y docstrings en español, mensajes de commit en inglés (convención del repo).

---

### Task 1: Scaffold del paquete y barrera anti-contaminación

Sin esto no hay dónde escribir ni test que correr. El hook va aquí y no al final porque su trabajo es impedir que un XML real entre al repo, y el riesgo empieza en el primer commit.

**Files:**
- Create: `pyproject.toml`
- Create: `src/ubl_star/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_version.py`
- Create: `.githooks/pre-commit`
- Modify: `.gitignore` (añadir el bloque de datos reales al final)

**Interfaces:**
- Consumes: nada.
- Produces: el paquete `ubl_star` importable con `ubl_star.__version__: str`.

- [ ] **Step 1: Escribir el test que falla**

`tests/test_version.py`:

```python
"""El paquete existe y se puede importar."""

import ubl_star


def test_paquete_declara_version() -> None:
    assert isinstance(ubl_star.__version__, str)
    assert ubl_star.__version__
```

- [ ] **Step 2: Correr el test y verlo fallar**

Run: `pytest tests/test_version.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'ubl_star'`

- [ ] **Step 3: Crear `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ubl-star"
version = "0.1.0"
description = "De factura electronica UBL 2.1 a hechos listos para analizar."
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Cristobal Salcedo", email = "support@pesanteanalytics.com" }]
keywords = ["invoice", "ubl", "dian", "peppol", "star-schema", "parquet"]

# Solo licencias permisivas, igual que pdfstar. Nada AGPL/GPL.
dependencies = [
    "pydantic>=2.7",      # MIT — contratos de datos
    "defusedxml>=0.7",    # PSF — parseo XML sin XXE ni billion-laughs
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov>=5",
    # CLAVADA, no `>=`: es un verificador cuyo veredicto cambia con la version.
    # Mismo criterio que pdfstar — si el hook local y el CI corren versiones
    # distintas, "verde en local" deja de significar nada.
    "ruff==0.15.4",
    "mypy>=1.11",
    "pyyaml>=6",          # MIT — lee el bloque declarativo del contrato en el test
]

[project.urls]
Homepage = "https://csalcedodatabi.com/"
Repository = "https://github.com/CSalcedoDataBI/ubl-star"

[tool.hatch.build.targets.wheel]
packages = ["src/ubl_star"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 4: Crear `src/ubl_star/__init__.py`**

```python
"""De factura electronica UBL 2.1 a hechos listos para analizar."""

__version__ = "0.1.0"
```

- [ ] **Step 5: Crear `tests/__init__.py` vacío**

```python
```

- [ ] **Step 6: Instalar e ir a verde**

Run:

```bash
pip install -e ".[dev]"
pytest tests/test_version.py -v
```

Expected: `1 passed`

- [ ] **Step 7: Escribir el hook anti-contaminación**

`.githooks/pre-commit` — rechaza cualquier XML, ZIP, PDF o imagen fuera de `tests/fixtures/`. Es la misma barrera que `pdfstar`, adaptada a que aquí el documento peligroso es el XML:

```sh
#!/bin/sh
# Barrera anti-contaminacion: ningun documento real entra a este repo publico.
#
# Aqui el archivo peligroso es el XML: una factura DIAN lleva nombre, NIT,
# cedula, direccion, correo y CUDE de personas reales. Las fixtures son
# sinteticas y se generan por codigo, asi que un documento fuera de
# tests/fixtures/ solo puede ser real.

fallo=0

for archivo in $(git diff --cached --name-only --diff-filter=A); do
    case "$archivo" in
        tests/fixtures/*)
            continue
            ;;
        *.xml|*.XML|*.zip|*.ZIP|*.pdf|*.PDF|*.png|*.PNG|*.jpg|*.JPG|*.jpeg|*.JPEG)
            echo "BLOQUEADO: $archivo — documento fuera de tests/fixtures/"
            fallo=1
            ;;
    esac
done

if [ "$fallo" -ne 0 ]; then
    echo ""
    echo "Las facturas reales no se versionan. Las fixtures son sinteticas y"
    echo "viven en tests/fixtures/. Si esto es una fixture, muevela alli."
    exit 1
fi

exit 0
```

- [ ] **Step 8: Activar el hook y verificarlo a mano**

Run:

```bash
git config core.hooksPath .githooks
```

Luego comprobar que atrapa lo que debe. El `-f` fuerza el paso del `.gitignore`, que es justo lo que el hook tiene que interceptar:

```bash
touch factura-real.xml
git add -f factura-real.xml && sh .githooks/pre-commit
git reset
rm factura-real.xml
```

Expected: `BLOQUEADO: factura-real.xml — documento fuera de tests/fixtures/` y exit 1.

Y que deja pasar la fixture:

```bash
mkdir -p tests/fixtures && touch tests/fixtures/sintetica.xml
git add -f tests/fixtures/sintetica.xml && sh .githooks/pre-commit
git reset
rm tests/fixtures/sintetica.xml
```

Expected: sin salida y exit 0.

- [ ] **Step 9: Añadir el bloque de datos reales a `.gitignore`**

Añadir al final del `.gitignore` existente:

```gitignore

# Datos reales — nunca. Las fixtures sinteticas de tests/fixtures/ estan exceptuadas
# abajo; todo lo demas queda fuera aunque alguien lo escriba por error.
*.xml
*.zip
*.pdf
!tests/fixtures/**/*.xml
!tests/fixtures/**/*.zip
```

- [ ] **Step 10: Commit**

```bash
git add pyproject.toml src tests .githooks .gitignore
git commit -m "feat: package scaffold and contamination guard hook"
```

---

### Task 2: El contrato de salida, declarado y anclado (issue #2)

El acuerdo se comparte como documento, no como código: este repo es público y la implementación hermana no lo es. El test de conformidad es lo que impide que las dos salidas deriven en silencio.

**Files:**
- Create: `docs/contrato/factura-v1.md`
- Create: `src/ubl_star/schema/__init__.py`
- Create: `tests/test_contrato.py`
- Create: `tests/test_schema.py`

**Interfaces:**
- Consumes: el paquete de la Task 1.
- Produces:
  - `ubl_star.schema.Invoice` — pydantic model. Campos: `numero_factura: str | None`, `cufe: str | None`, `fecha_emision: date | None`, `fecha_vencimiento: date | None`, `proveedor_nombre: str | None`, `proveedor_id_fiscal: str | None`, `cliente_nombre: str | None`, `cliente_id_fiscal: str | None`, `moneda: str | None`, `subtotal: Dinero | None`, `impuesto_total: Dinero | None`, `total: Dinero | None`, `orden_compra: str | None`, `lineas: list[InvoiceLine]`, `extras: dict[str, Any]`.
  - `ubl_star.schema.InvoiceLine` — campos: `descripcion`, `cantidad`, `precio_unitario`, `importe`, `codigo`, `extras`.
  - `ubl_star.schema.Problema` — campos `campo: str`, `detalle: str`.
  - `ubl_star.schema.Dinero` — `Annotated[Decimal, BeforeValidator]` que rechaza `float`.
  - `ubl_star.schema.TOLERANCIA: Decimal` = `Decimal("0.02")`.
  - `Invoice.problemas() -> list[Problema]`, `Invoice.cuadra() -> bool`, `InvoiceLine.problemas() -> list[Problema]`.

- [ ] **Step 1: Escribir el documento del contrato**

`docs/contrato/factura-v1.md`. El bloque `yaml` no es decoración: es lo que lee el test de conformidad.

````markdown
# Contrato de salida — factura v1

Este documento **es** el contrato. Cualquier implementación que lea facturas de
cualquier fuente —XML UBL, PDF nativo, escaneado— y produzca estas tablas con
estos campos es intercambiable aguas abajo con `ubl-star`, sin compartir una
línea de código.

`tests/test_contrato.py` falla si el modelo de este repo se aparta del bloque de
abajo. Ese test es la única razón por la que este documento no se queda viejo.

## Versión

`1`. Un cambio que quite un campo, le cambie el tipo o le cambie el nombre es
**ruptura** y sube a v2. Añadir un campo opcional no rompe: un consumidor que no
lo conoce lo ignora.

## Reglas transversales

- **El dinero es `Decimal`.** El contrato rechaza `float` en cualquier importe.
- **Un campo ausente es `None`**, nunca un cero, nunca una cadena vacía, nunca un
  valor inferido.
- **`extras` es el cajón de lo que no es canónico.** Campos propios del emisor o
  del perfil fiscal van ahí y no sueltos en el modelo, para que el contrato siga
  siendo cerrado.

## Coherencia

Una factura *cuadra* cuando `total == subtotal + impuesto_total` dentro de una
tolerancia de `0.02`, y cuando `fecha_vencimiento >= fecha_emision`. Una línea
cuadra cuando `importe == cantidad * precio_unitario` con la misma tolerancia.

Que cuadre no significa que los valores sean correctos: significa que el
documento es consistente consigo mismo.

**Descuentos y anticipos no entran en esa identidad.** En UBL, lo que se paga es
`LineExtensionAmount + TaxAmount − AllowanceTotalAmount + ChargeTotalAmount −
PrepaidAmount`. El campo `total` del contrato es el total **con impuestos y antes
de descuentos**; lo pagadero vive en `extras`. Meter el pagadero en `total`
convertiría cada subsidio en un descuadre falso.

## Campos

```yaml
invoice:
  numero_factura: str | null
  cufe: str | null
  fecha_emision: date | null
  fecha_vencimiento: date | null
  proveedor_nombre: str | null
  proveedor_id_fiscal: str | null
  cliente_nombre: str | null
  cliente_id_fiscal: str | null
  moneda: str | null
  subtotal: money | null
  impuesto_total: money | null
  total: money | null
  orden_compra: str | null
  lineas: list[invoice_line]
  extras: dict
invoice_line:
  descripcion: str | null
  cantidad: money | null
  precio_unitario: money | null
  importe: money | null
  codigo: str | null
  extras: dict
```
````

- [ ] **Step 2: Escribir el test de conformidad, que falla**

`tests/test_contrato.py`:

```python
"""El modelo no se aparta del documento del contrato.

Este test es la razon por la que docs/contrato/factura-v1.md no se queda viejo:
si alguien anade un campo al modelo y no al documento, esto falla.
"""

import re
from pathlib import Path

import yaml

from ubl_star.schema import Invoice, InvoiceLine

CONTRATO = Path(__file__).resolve().parents[1] / "docs" / "contrato" / "factura-v1.md"


def _campos_declarados() -> dict[str, dict[str, str]]:
    """Lee el unico bloque yaml del documento del contrato."""
    texto = CONTRATO.read_text(encoding="utf-8")
    bloques = re.findall(r"```yaml\n(.*?)```", texto, re.DOTALL)
    assert len(bloques) == 1, f"se esperaba exactamente un bloque yaml, hay {len(bloques)}"
    return yaml.safe_load(bloques[0])


def test_invoice_tiene_exactamente_los_campos_del_contrato() -> None:
    declarados = set(_campos_declarados()["invoice"])
    assert set(Invoice.model_fields) == declarados


def test_invoice_line_tiene_exactamente_los_campos_del_contrato() -> None:
    declarados = set(_campos_declarados()["invoice_line"])
    assert set(InvoiceLine.model_fields) == declarados
```

- [ ] **Step 3: Correr y verlo fallar**

Run: `pytest tests/test_contrato.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'ubl_star.schema'`

- [ ] **Step 4: Escribir el contrato en código**

`src/ubl_star/schema/__init__.py`. Es deliberadamente el mismo contrato que declara la implementación hermana: la duplicación es el precio de no depender de un paquete privado desde uno público, y el test de conformidad de arriba es lo que impide que las dos copias deriven.

```python
"""Los contratos: que es exactamente una factura para ubl-star.

La forma la declara `docs/contrato/factura-v1.md` y `tests/test_contrato.py`
ancla este modulo a ese documento. No se toca uno sin el otro.

El dinero va en `Decimal` y el contrato rechaza `float`: esto termina en
contabilidad y `0.1 + 0.2 != 0.3` en float.
"""

from datetime import date
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

TOLERANCIA = Decimal("0.02")
"""Margen para el redondeo del emisor. No es un descuadre que merezca atencion."""


def _rechaza_float(v: Any) -> Any:
    """Un float ya perdio precision antes de llegar aqui.

    `Decimal(0.1)` no es `0.1`, y pydantic disimula el destrozo convirtiendo el
    float por su repr. Quien tenga un float debe pasar el texto original.
    """
    if isinstance(v, float):
        raise ValueError(
            f"{v!r} es un float y el dinero no pasa por float: usa Decimal o el texto original"
        )
    return v


Dinero = Annotated[Decimal, BeforeValidator(_rechaza_float)]
"""Un importe. Acepta texto, entero o Decimal; nunca float."""


class Problema(BaseModel):
    """Una incoherencia concreta, con el campo al que culpa."""

    campo: str
    detalle: str

    def __str__(self) -> str:
        return f"{self.campo}: {self.detalle}"


class _Base(BaseModel):
    # extra='forbid': un campo canonico mal escrito debe reventar, no colarse.
    # validate_assignment: el contrato vale tambien DESPUES de construir.
    model_config = ConfigDict(populate_by_name=True, extra="forbid", validate_assignment=True)

    extras: dict[str, Any] = Field(default_factory=dict)
    """Campos propios del emisor o del perfil fiscal. Cajon aparte, no sueltos."""


class InvoiceLine(_Base):
    """Una linea de detalle. El grano de `fact_factura_linea`."""

    descripcion: str | None = Field(default=None, alias="linea_descripcion")
    cantidad: Dinero | None = Field(default=None, alias="linea_cantidad")
    precio_unitario: Dinero | None = Field(default=None, alias="linea_precio_unitario")
    importe: Dinero | None = Field(default=None, alias="linea_importe")
    codigo: str | None = Field(default=None, alias="linea_codigo")

    def problemas(self) -> list[Problema]:
        """Incoherencias de la linea. Lista vacia = la linea cuadra."""
        if self.cantidad is None or self.precio_unitario is None or self.importe is None:
            # Un hueco no es una incoherencia: es un campo que nadie leyo.
            return []

        esperado = self.cantidad * self.precio_unitario
        if abs(self.importe - esperado) > TOLERANCIA:
            return [
                Problema(
                    campo="linea_importe",
                    detalle=(
                        f"{self.importe} no cuadra con cantidad x precio_unitario "
                        f"({self.cantidad} x {self.precio_unitario} = {esperado})"
                    ),
                )
            ]
        return []


class Invoice(_Base):
    """Una factura: cabecera + lineas de detalle."""

    numero_factura: str | None = None
    cufe: str | None = None
    fecha_emision: date | None = None
    fecha_vencimiento: date | None = None
    proveedor_nombre: str | None = None
    proveedor_id_fiscal: str | None = None
    cliente_nombre: str | None = None
    cliente_id_fiscal: str | None = None
    moneda: str | None = None
    subtotal: Dinero | None = None
    impuesto_total: Dinero | None = None
    total: Dinero | None = None
    orden_compra: str | None = None

    lineas: list[InvoiceLine] = Field(default_factory=list)

    def problemas(self) -> list[Problema]:
        """Todas las incoherencias de la factura, incluidas las de sus lineas."""
        encontrados: list[Problema] = []

        if self.subtotal is not None and self.impuesto_total is not None and self.total is not None:
            esperado = self.subtotal + self.impuesto_total
            if abs(self.total - esperado) > TOLERANCIA:
                encontrados.append(
                    Problema(
                        campo="total",
                        detalle=(
                            f"{self.total} no cuadra con subtotal + impuesto_total "
                            f"({self.subtotal} + {self.impuesto_total} = {esperado})"
                        ),
                    )
                )

        if self.fecha_emision and self.fecha_vencimiento:
            if self.fecha_vencimiento < self.fecha_emision:
                encontrados.append(
                    Problema(
                        campo="fecha_vencimiento",
                        detalle=(
                            f"{self.fecha_vencimiento} es anterior a la emision "
                            f"({self.fecha_emision})"
                        ),
                    )
                )

        # La linea se numera como la lee un humano en el papel: la primera es la 1.
        for i, linea in enumerate(self.lineas, start=1):
            for p in linea.problemas():
                encontrados.append(Problema(campo=f"lineas[{i}].{p.campo}", detalle=p.detalle))

        return encontrados

    def cuadra(self) -> bool:
        """Atajo legible para el camino feliz."""
        return not self.problemas()
```

- [ ] **Step 5: Correr el test de conformidad**

Run: `pytest tests/test_contrato.py -v`
Expected: `2 passed`

- [ ] **Step 6: Escribir los tests del comportamiento del contrato**

`tests/test_schema.py`:

```python
"""El contrato se comporta como dice el documento."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ubl_star.schema import Invoice, InvoiceLine


def test_el_dinero_rechaza_float() -> None:
    with pytest.raises(ValidationError, match="no pasa por float"):
        Invoice(total=1234.56)  # type: ignore[arg-type]


def test_el_dinero_acepta_el_texto_original() -> None:
    assert Invoice(total="1234.56").total == Decimal("1234.56")


def test_un_campo_canonico_mal_escrito_revienta() -> None:
    with pytest.raises(ValidationError):
        Invoice(numero_factra="X-1")  # type: ignore[call-arg]


def test_los_extras_no_revientan() -> None:
    factura = Invoice(extras={"contrato": "99999999"})
    assert factura.extras["contrato"] == "99999999"


def test_total_que_no_cuadra_se_reporta_sin_reventar() -> None:
    factura = Invoice(subtotal="100.00", impuesto_total="19.00", total="200.00")
    problemas = factura.problemas()
    assert len(problemas) == 1
    assert problemas[0].campo == "total"
    assert not factura.cuadra()


def test_total_dentro_de_la_tolerancia_cuadra() -> None:
    factura = Invoice(subtotal="100.00", impuesto_total="18.99", total="119.00")
    assert factura.cuadra()


def test_vencimiento_anterior_a_la_emision_se_reporta() -> None:
    factura = Invoice(fecha_emision=date(2026, 3, 24), fecha_vencimiento=date(2026, 3, 1))
    assert [p.campo for p in factura.problemas()] == ["fecha_vencimiento"]


def test_linea_que_no_cuadra_se_reporta_con_su_indice_humano() -> None:
    factura = Invoice(
        lineas=[
            InvoiceLine(cantidad="1", precio_unitario="10.00", importe="10.00"),
            InvoiceLine(cantidad="2", precio_unitario="10.00", importe="99.00"),
        ]
    )
    assert [p.campo for p in factura.problemas()] == ["lineas[2].linea_importe"]


def test_una_linea_incompleta_no_es_una_incoherencia() -> None:
    """Un hueco es un campo que nadie leyo, no un descuadre."""
    assert InvoiceLine(cantidad="1", importe="10.00").problemas() == []


def test_un_campo_ausente_es_none_no_cero() -> None:
    assert Invoice().total is None
```

- [ ] **Step 7: Correr todo y quedar verde**

Run: `pytest tests/ -v`
Expected: todos pasan.

- [ ] **Step 8: Commit**

```bash
git add docs/contrato src/ubl_star/schema tests/test_contrato.py tests/test_schema.py
git commit -m "feat: versioned output contract with conformance test (closes #2)"
```

---

### Task 3: Fixture sintética del perfil DIAN SPD

El parser necesita algo contra qué correr, y ese algo no puede ser una factura real. La fixture se **genera por código** para que se vea que cada valor es inventado.

**Files:**
- Create: `tests/fixtures/generar.py`
- Create: `tests/fixtures/dian_spd_601.xml` (generado, versionado)
- Create: `tests/test_fixtures.py`

**Interfaces:**
- Consumes: nada del paquete.
- Produces:
  - `tests/fixtures/generar.py::construir_adjunto_spd() -> str` — devuelve el XML del `AttachedDocument` completo.
  - `tests/fixtures/dian_spd_601.xml` — la fixture en disco, que las Tasks 4 y 5 leen.

- [ ] **Step 1: Escribir el generador**

`tests/fixtures/generar.py`. Reproduce la estructura real del perfil —`AttachedDocument` con el `Invoice` embebido en CDATA, notas `languageLocaleID`, `AllowanceCharge` de subsidio, líneas con `InvoicedQuantity` fija en 1— con emisor, NIT, cédula, contrato y valores **inventados**:

```python
"""Fabrica las fixtures sinteticas. Ningun valor de aqui es real.

Se genera por codigo y no se escribe a mano para que sea evidente que cada NIT,
cada nombre y cada importe salio de esta funcion y no de la factura de nadie.

La estructura si es la de verdad: AttachedDocument con el Invoice embebido en
CDATA, notas por `languageLocaleID`, subsidios como AllowanceCharge de cabecera
y lineas con `InvoicedQuantity` fija en 1.00 llevando el importe entero en
`PriceAmount`. Eso ultimo es lo que caracteriza al Documento Equivalente SPD
(CustomizationID 601): el XML lleva la plata por concepto, no el consumo fisico.
"""

from pathlib import Path

AQUI = Path(__file__).resolve().parent

# Todo inventado. NIT 800.111.222 y cedula 10000001 no corresponden a nadie.
_INVOICE = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" \
xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" \
xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">\
<cbc:UBLVersionID>UBL 2.1</cbc:UBLVersionID>\
<cbc:CustomizationID>601</cbc:CustomizationID>\
<cbc:ProfileID>DIAN 2.1: Documento Equivalente SPD</cbc:ProfileID>\
<cbc:ID>DEE00000001</cbc:ID>\
<cbc:UUID schemeID="1" schemeName="CUDE-SHA384">abc123def456</cbc:UUID>\
<cbc:IssueDate>2026-01-15</cbc:IssueDate>\
<cbc:IssueTime>04:00:00-05:00</cbc:IssueTime>\
<cbc:InvoiceTypeCode>60</cbc:InvoiceTypeCode>\
<cbc:Note languageLocaleID="contrato">99999999</cbc:Note>\
<cbc:Note languageLocaleID="corte">17</cbc:Note>\
<cbc:Note languageLocaleID="Cuota Financiacion">1000.00</cbc:Note>\
<cbc:DocumentCurrencyCode>COP</cbc:DocumentCurrencyCode>\
<cbc:LineCountNumeric>2</cbc:LineCountNumeric>\
<cac:AccountingSupplierParty><cac:Party>\
<cac:PartyTaxScheme><cbc:RegistrationName>SERVICIOS PUBLICOS EJEMPLO E.S.P.</cbc:RegistrationName>\
<cbc:CompanyID schemeID="1" schemeName="31">800111222</cbc:CompanyID>\
</cac:PartyTaxScheme>\
<cac:PartyLegalEntity><cbc:RegistrationName>SERVICIOS PUBLICOS EJEMPLO E.S.P.</cbc:RegistrationName>\
<cbc:CompanyID schemeID="1" schemeName="31">800111222</cbc:CompanyID>\
</cac:PartyLegalEntity></cac:Party></cac:AccountingSupplierParty>\
<cac:AccountingCustomerParty><cbc:CustomerAssignedAccountID>99999999</cbc:CustomerAssignedAccountID>\
<cac:Party>\
<cac:PartyLegalEntity><cbc:RegistrationName>PERSONA DE PRUEBA</cbc:RegistrationName>\
<cbc:CompanyID schemeID="0" schemeName="13">10000001</cbc:CompanyID>\
</cac:PartyLegalEntity></cac:Party></cac:AccountingCustomerParty>\
<cac:PaymentMeans><cbc:ID>2</cbc:ID><cbc:PaymentMeansCode>ZZZ</cbc:PaymentMeansCode>\
<cbc:PaymentDueDate>2026-02-05</cbc:PaymentDueDate></cac:PaymentMeans>\
<cac:AllowanceCharge><cbc:ID schemeName="2">1</cbc:ID>\
<cbc:ChargeIndicator>false</cbc:ChargeIndicator>\
<cbc:AllowanceChargeReasonCode>01</cbc:AllowanceChargeReasonCode>\
<cbc:AllowanceChargeReason>SUBSIDIO</cbc:AllowanceChargeReason>\
<cbc:MultiplierFactorNumeric>10.00</cbc:MultiplierFactorNumeric>\
<cbc:Amount currencyID="COP">3000.00</cbc:Amount>\
<cbc:BaseAmount currencyID="COP">30190.00</cbc:BaseAmount></cac:AllowanceCharge>\
<cac:TaxTotal><cbc:TaxAmount currencyID="COP">190.00</cbc:TaxAmount>\
<cac:TaxSubtotal><cbc:TaxableAmount currencyID="COP">1000.00</cbc:TaxableAmount>\
<cbc:TaxAmount currencyID="COP">190.00</cbc:TaxAmount>\
<cac:TaxCategory><cbc:Percent>19.00</cbc:Percent>\
<cac:TaxScheme><cbc:ID>01</cbc:ID><cbc:Name>IVA</cbc:Name></cac:TaxScheme>\
</cac:TaxCategory></cac:TaxSubtotal></cac:TaxTotal>\
<cac:LegalMonetaryTotal>\
<cbc:LineExtensionAmount currencyID="COP">30000.00</cbc:LineExtensionAmount>\
<cbc:TaxExclusiveAmount currencyID="COP">1000.00</cbc:TaxExclusiveAmount>\
<cbc:TaxInclusiveAmount currencyID="COP">30190.00</cbc:TaxInclusiveAmount>\
<cbc:AllowanceTotalAmount currencyID="COP">3000.00</cbc:AllowanceTotalAmount>\
<cbc:ChargeTotalAmount currencyID="COP">0.00</cbc:ChargeTotalAmount>\
<cbc:PrepaidAmount currencyID="COP">0.00</cbc:PrepaidAmount>\
<cbc:PayableRoundingAmount currencyID="COP">0.00</cbc:PayableRoundingAmount>\
<cbc:PayableAmount currencyID="COP">27190.00</cbc:PayableAmount>\
</cac:LegalMonetaryTotal>\
<cac:InvoiceLine><cbc:ID schemeID="0">1</cbc:ID>\
<cbc:InvoicedQuantity unitCode="KWH">1.00</cbc:InvoicedQuantity>\
<cbc:LineExtensionAmount currencyID="COP">20000.00</cbc:LineExtensionAmount>\
<cbc:AccountingCostCode>111111111</cbc:AccountingCostCode>\
<cac:Item><cbc:Description>ENERGIA MDO REGULADO</cbc:Description>\
<cac:StandardItemIdentification><cbc:ID schemeID="999">90</cbc:ID>\
</cac:StandardItemIdentification></cac:Item>\
<cac:Price><cbc:PriceAmount currencyID="COP">20000.00</cbc:PriceAmount>\
<cbc:BaseQuantity unitCode="KWH">1.00</cbc:BaseQuantity></cac:Price></cac:InvoiceLine>\
<cac:InvoiceLine><cbc:ID schemeID="0">2</cbc:ID>\
<cbc:InvoicedQuantity unitCode="MTQ">1.00</cbc:InvoicedQuantity>\
<cbc:LineExtensionAmount currencyID="COP">10000.00</cbc:LineExtensionAmount>\
<cbc:AccountingCostCode>222222222</cbc:AccountingCostCode>\
<cac:Item><cbc:Description>AGUA POTABLE</cbc:Description>\
<cac:StandardItemIdentification><cbc:ID schemeID="999">87</cbc:ID>\
</cac:StandardItemIdentification></cac:Item>\
<cac:Price><cbc:PriceAmount currencyID="COP">10000.00</cbc:PriceAmount>\
<cbc:BaseQuantity unitCode="MTQ">1.00</cbc:BaseQuantity></cac:Price></cac:InvoiceLine>\
</Invoice>"""


def construir_adjunto_spd() -> str:
    """El AttachedDocument con el Invoice embebido en CDATA, como lo emite la DIAN."""
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        "<AttachedDocument "
        'xmlns="urn:oasis:names:specification:ubl:schema:xsd:AttachedDocument-2" '
        'xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" '
        'xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">'
        "<cbc:ID>DEE00000001</cbc:ID>"
        "<cac:Attachment><cac:ExternalReference>"
        "<cbc:Description><![CDATA[" + _INVOICE + "]]></cbc:Description>"
        "</cac:ExternalReference></cac:Attachment>"
        "</AttachedDocument>"
    )


def main() -> None:
    (AQUI / "dian_spd_601.xml").write_text(construir_adjunto_spd(), encoding="utf-8")
    print("escrita dian_spd_601.xml")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Generar la fixture**

Run: `python tests/fixtures/generar.py`
Expected: `escrita dian_spd_601.xml`

- [ ] **Step 3: Escribir el test que ancla la fixture al generador**

`tests/test_fixtures.py`:

```python
"""La fixture en disco es exactamente lo que produce el generador.

Si alguien la edita a mano, esto lo dice. Es tambien lo que garantiza que no se
cuele un valor real dentro de un archivo que parece sintetico.
"""

from pathlib import Path

from tests.fixtures.generar import construir_adjunto_spd

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_la_fixture_coincide_con_su_generador() -> None:
    en_disco = (FIXTURES / "dian_spd_601.xml").read_text(encoding="utf-8")
    assert en_disco == construir_adjunto_spd()
```

- [ ] **Step 4: Crear `tests/fixtures/__init__.py` vacío para que el import funcione**

```python
```

- [ ] **Step 5: Correr y quedar verde**

Run: `pytest tests/test_fixtures.py -v`
Expected: `1 passed`

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures tests/test_fixtures.py
git commit -m "test: synthetic DIAN SPD 601 fixture generated from code"
```

---

### Task 4: Entrada real — el ZIP del adjunto (issue #4)

**Files:**
- Create: `src/ubl_star/zip.py`
- Create: `tests/test_zip.py`

**Interfaces:**
- Consumes: `tests/fixtures/generar.py::construir_adjunto_spd`.
- Produces:
  - `ubl_star.zip.localizar_xml(ruta: Path) -> str` — devuelve el texto del XML de la factura. Si `ruta` es un `.xml` lo lee; si es un `.zip`, encuentra dentro el XML de la factura entre los demás documentos. Lanza `SinFacturaEnAdjunto` si no hay ninguno, y `AdjuntoAmbiguo` si hay más de uno.
  - `ubl_star.zip.SinFacturaEnAdjunto(Exception)`
  - `ubl_star.zip.AdjuntoAmbiguo(Exception)`

- [ ] **Step 1: Escribir los tests que fallan**

`tests/test_zip.py`:

```python
"""El adjunto: encontrar el XML de la factura entre lo demas."""

import zipfile
from pathlib import Path

import pytest

from tests.fixtures.generar import construir_adjunto_spd
from ubl_star.zip import AdjuntoAmbiguo, SinFacturaEnAdjunto, localizar_xml


def _zip_con(tmp_path: Path, **archivos: bytes) -> Path:
    destino = tmp_path / "adjunto.zip"
    with zipfile.ZipFile(destino, "w") as z:
        for nombre, contenido in archivos.items():
            z.writestr(nombre.replace("__", "."), contenido)
    return destino


def test_un_xml_suelto_se_lee_tal_cual(tmp_path: Path) -> None:
    ruta = tmp_path / "factura.xml"
    ruta.write_text(construir_adjunto_spd(), encoding="utf-8")
    assert localizar_xml(ruta) == construir_adjunto_spd()


def test_encuentra_el_xml_dentro_del_zip(tmp_path: Path) -> None:
    ruta = _zip_con(
        tmp_path,
        ad089__xml=construir_adjunto_spd().encode("utf-8"),
        ds089__pdf=b"%PDF-1.4 no soy un xml",
    )
    assert localizar_xml(ruta) == construir_adjunto_spd()


def test_un_zip_sin_xml_lo_dice(tmp_path: Path) -> None:
    ruta = _zip_con(tmp_path, ds089__pdf=b"%PDF-1.4")
    with pytest.raises(SinFacturaEnAdjunto):
        localizar_xml(ruta)


def test_un_zip_con_dos_xml_no_adivina(tmp_path: Path) -> None:
    """Elegir uno seria inventar. Se reporta y decide quien llama."""
    ruta = _zip_con(
        tmp_path,
        uno__xml=construir_adjunto_spd().encode("utf-8"),
        dos__xml=construir_adjunto_spd().encode("utf-8"),
    )
    with pytest.raises(AdjuntoAmbiguo):
        localizar_xml(ruta)


def test_ignora_lo_que_no_es_xml_ni_por_extension_ni_por_carpeta(tmp_path: Path) -> None:
    ruta = _zip_con(
        tmp_path,
        **{
            "docs/leeme__txt": b"nada",
            "ad089__xml": construir_adjunto_spd().encode("utf-8"),
        },
    )
    assert localizar_xml(ruta) == construir_adjunto_spd()
```

- [ ] **Step 2: Correr y verlo fallar**

Run: `pytest tests/test_zip.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'ubl_star.zip'`

- [ ] **Step 3: Implementar**

`src/ubl_star/zip.py`:

```python
"""La entrada real: lo que llega es un ZIP, no un XML suelto.

La DIAN entrega el adjunto como un ZIP con el XML firmado y su representacion
grafica en PDF. Este modulo hace una sola cosa: devolver el texto del XML de la
factura. Si hay mas de uno, no elige — elegir seria inventar.
"""

import zipfile
from pathlib import Path


class SinFacturaEnAdjunto(Exception):
    """El adjunto no trae ningun XML."""


class AdjuntoAmbiguo(Exception):
    """El adjunto trae mas de un XML y ninguna regla dice cual es la factura."""


def localizar_xml(ruta: Path) -> str:
    """Devuelve el texto del XML de la factura, venga suelto o dentro del ZIP."""
    ruta = Path(ruta)

    if ruta.suffix.lower() == ".xml":
        return ruta.read_text(encoding="utf-8")

    with zipfile.ZipFile(ruta) as adjunto:
        candidatos = [
            nombre
            for nombre in adjunto.namelist()
            if nombre.lower().endswith(".xml") and not nombre.endswith("/")
        ]

        if not candidatos:
            raise SinFacturaEnAdjunto(f"{ruta.name} no contiene ningun XML")
        if len(candidatos) > 1:
            raise AdjuntoAmbiguo(
                f"{ruta.name} contiene {len(candidatos)} XML y ninguna regla dice "
                f"cual es la factura: {', '.join(sorted(candidatos))}"
            )

        return adjunto.read(candidatos[0]).decode("utf-8")
```

- [ ] **Step 4: Correr y quedar verde**

Run: `pytest tests/test_zip.py -v`
Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/ubl_star/zip.py tests/test_zip.py
git commit -m "feat: locate the invoice XML inside the DIAN attachment zip (closes #4)"
```

---

### Task 5: Parser UBL 2.1 — desanidar y mapear (issue #3)

El corazón. Cada campo sale de su ruta del estándar; lo que no está, no está.

**Files:**
- Create: `src/ubl_star/parser.py`
- Create: `tests/test_parser.py`

**Interfaces:**
- Consumes: `ubl_star.schema.Invoice`, `ubl_star.schema.InvoiceLine`, `ubl_star.zip.localizar_xml`.
- Produces:
  - `ubl_star.parser.desanidar(xml: str) -> str` — si el documento es un `AttachedDocument`, devuelve el `Invoice` embebido en CDATA; si ya es un `Invoice`, lo devuelve tal cual.
  - `ubl_star.parser.parsear(xml: str) -> Invoice` — el mapeo completo.
  - `ubl_star.parser.leer(ruta: Path) -> Invoice` — `localizar_xml` + `desanidar` + `parsear`.
  - `ubl_star.parser.NoEsUnaFactura(Exception)`

**Mapeo — cada campo con su ruta.** El parser implementa exactamente esta tabla:

| Campo del contrato | Ruta UBL |
|---|---|
| `numero_factura` | `/Invoice/cbc:ID` |
| `cufe` | `/Invoice/cbc:UUID` |
| `fecha_emision` | `/Invoice/cbc:IssueDate` |
| `fecha_vencimiento` | `/Invoice/cac:PaymentMeans/cbc:PaymentDueDate` |
| `proveedor_nombre` | `/Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName` |
| `proveedor_id_fiscal` | `/Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID` |
| `cliente_nombre` | `/Invoice/cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName` |
| `cliente_id_fiscal` | `/Invoice/cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID` |
| `moneda` | `/Invoice/cbc:DocumentCurrencyCode` |
| `subtotal` | `/Invoice/cac:LegalMonetaryTotal/cbc:LineExtensionAmount` |
| `impuesto_total` | `/Invoice/cac:TaxTotal/cbc:TaxAmount` |
| `total` | `/Invoice/cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount` |
| `lineas[].descripcion` | `cac:Item/cbc:Description` |
| `lineas[].cantidad` | `cbc:InvoicedQuantity` |
| `lineas[].precio_unitario` | `cac:Price/cbc:PriceAmount` |
| `lineas[].importe` | `cbc:LineExtensionAmount` |
| `lineas[].codigo` | `cac:Item/cac:StandardItemIdentification/cbc:ID` |

`total` es `TaxInclusiveAmount` y **no** `PayableAmount`, por lo que dice el contrato: lo pagadero resta descuentos y meterlo en `total` convertiría cada subsidio en un descuadre falso. `PayableAmount` va a `extras`.

**A `extras` de la factura:** `ubl_customization_id`, `ubl_profile_id`, `ubl_invoice_type_code`, `ubl_payable_amount`, `ubl_allowance_total`, `ubl_charge_total`, `ubl_prepaid_amount`, `ubl_tax_exclusive_amount`, `notas` (dict de `cbc:Note` por su `languageLocaleID`) y `descuentos` (lista de dicts con `id`, `razon`, `codigo_razon`, `porcentaje`, `importe`, `base`).

**A `extras` de cada línea:** `unidad` (el `unitCode` de `InvoicedQuantity`) y `cuenta` (`cbc:AccountingCostCode`).

- [ ] **Step 1: Escribir los tests que fallan**

`tests/test_parser.py`:

```python
"""El parser: cada campo por su ruta del estandar, sin adivinar."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from tests.fixtures.generar import construir_adjunto_spd
from ubl_star.parser import NoEsUnaFactura, desanidar, leer, parsear


@pytest.fixture
def factura():
    return parsear(desanidar(construir_adjunto_spd()))


def test_desanida_el_invoice_del_attached_document() -> None:
    interno = desanidar(construir_adjunto_spd())
    assert "<Invoice" in interno
    assert "AttachedDocument" not in interno


def test_un_invoice_suelto_pasa_sin_tocarlo() -> None:
    interno = desanidar(construir_adjunto_spd())
    assert desanidar(interno) == interno


def test_un_xml_que_no_es_factura_lo_dice() -> None:
    with pytest.raises(NoEsUnaFactura):
        desanidar("<?xml version='1.0'?><OtraCosa/>")


def test_cabecera(factura) -> None:
    assert factura.numero_factura == "DEE00000001"
    assert factura.cufe == "abc123def456"
    assert factura.fecha_emision == date(2026, 1, 15)
    assert factura.fecha_vencimiento == date(2026, 2, 5)
    assert factura.moneda == "COP"


def test_partes(factura) -> None:
    assert factura.proveedor_nombre == "SERVICIOS PUBLICOS EJEMPLO E.S.P."
    assert factura.proveedor_id_fiscal == "800111222"
    assert factura.cliente_nombre == "PERSONA DE PRUEBA"
    assert factura.cliente_id_fiscal == "10000001"


def test_totales_en_decimal(factura) -> None:
    assert factura.subtotal == Decimal("30000.00")
    assert factura.impuesto_total == Decimal("190.00")
    assert factura.total == Decimal("30190.00")
    assert isinstance(factura.total, Decimal)


def test_la_factura_cuadra_consigo_misma(factura) -> None:
    """subtotal + impuesto == total. Los descuentos no entran en esa identidad."""
    assert factura.cuadra(), factura.problemas()


def test_lo_pagadero_va_a_extras_no_a_total(factura) -> None:
    assert factura.extras["ubl_payable_amount"] == Decimal("27190.00")
    assert factura.extras["ubl_allowance_total"] == Decimal("3000.00")


def test_las_notas_del_perfil_spd_van_a_extras(factura) -> None:
    assert factura.extras["notas"]["contrato"] == "99999999"
    assert factura.extras["notas"]["corte"] == "17"
    assert factura.extras["notas"]["Cuota Financiacion"] == "1000.00"


def test_los_subsidios_van_a_extras_con_su_razon(factura) -> None:
    descuentos = factura.extras["descuentos"]
    assert len(descuentos) == 1
    assert descuentos[0]["razon"] == "SUBSIDIO"
    assert descuentos[0]["porcentaje"] == Decimal("10.00")
    assert descuentos[0]["importe"] == Decimal("3000.00")


def test_lineas(factura) -> None:
    assert len(factura.lineas) == 2
    primera = factura.lineas[0]
    assert primera.descripcion == "ENERGIA MDO REGULADO"
    assert primera.codigo == "90"
    assert primera.cantidad == Decimal("1.00")
    assert primera.precio_unitario == Decimal("20000.00")
    assert primera.importe == Decimal("20000.00")


def test_la_unidad_y_la_cuenta_de_la_linea_van_a_extras(factura) -> None:
    assert factura.lineas[0].extras["unidad"] == "KWH"
    assert factura.lineas[0].extras["cuenta"] == "111111111"
    assert factura.lineas[1].extras["unidad"] == "MTQ"


def test_un_campo_opcional_ausente_es_none_no_una_excepcion() -> None:
    """El perfil SPD no trae orden de compra. Ausente es None, no un invento."""
    factura = parsear(desanidar(construir_adjunto_spd()))
    assert factura.orden_compra is None


def test_leer_acepta_la_ruta_de_un_zip(tmp_path: Path) -> None:
    import zipfile

    destino = tmp_path / "adjunto.zip"
    with zipfile.ZipFile(destino, "w") as z:
        z.writestr("ad.xml", construir_adjunto_spd())
        z.writestr("ds.pdf", b"%PDF-1.4")

    assert leer(destino).numero_factura == "DEE00000001"
```

- [ ] **Step 2: Correr y verlo fallar**

Run: `pytest tests/test_parser.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'ubl_star.parser'`

- [ ] **Step 3: Implementar**

`src/ubl_star/parser.py`:

```python
"""XML UBL 2.1 -> el contrato Invoice. Cada campo por su ruta del estandar.

Dos pasos, deliberadamente separados:

- `desanidar` resuelve que la DIAN no entrega el Invoice suelto: lo embebe en
  CDATA dentro de un AttachedDocument junto con la respuesta del validador.
- `parsear` mapea. No calcula, no infiere, no rellena: si un campo no esta en el
  XML, el contrato lo recibe como None.

Se usa defusedxml y no la stdlib a secas porque esto lee documentos que llegan
de un tercero, y `xml.etree` es vulnerable a entidades expansivas.
"""

import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

from defusedxml.ElementTree import fromstring

from ubl_star.schema import Invoice, InvoiceLine
from ubl_star.zip import localizar_xml

NS = {
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}

_CDATA = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.DOTALL)


class NoEsUnaFactura(Exception):
    """El XML no es un Invoice ni un AttachedDocument que lo contenga."""


def desanidar(xml: str) -> str:
    """Devuelve el Invoice. Si viene embebido en un AttachedDocument, lo saca.

    El AttachedDocument lleva dos bloques CDATA: el Invoice y la
    ApplicationResponse del validador. Se busca el que sea una factura en vez de
    tomar el primero por posicion, porque el orden no lo garantiza el estandar.
    """
    if "<Invoice" in xml and "<AttachedDocument" not in xml:
        return xml

    for bloque in _CDATA.findall(xml):
        if "<Invoice" in bloque:
            return bloque

    raise NoEsUnaFactura("el XML no es un Invoice ni contiene uno embebido")


def _texto(nodo: Element | None, ruta: str) -> str | None:
    """El texto de una ruta, o None si no esta. Nunca una cadena vacia."""
    if nodo is None:
        return None
    encontrado = nodo.find(ruta, NS)
    if encontrado is None or encontrado.text is None:
        return None
    valor = encontrado.text.strip()
    return valor or None


def _dinero(nodo: Element | None, ruta: str) -> Decimal | None:
    """Un importe como Decimal, leido del texto tal cual esta escrito."""
    crudo = _texto(nodo, ruta)
    return Decimal(crudo) if crudo is not None else None


def _fecha(nodo: Element | None, ruta: str) -> date | None:
    crudo = _texto(nodo, ruta)
    return date.fromisoformat(crudo) if crudo is not None else None


def _atributo(nodo: Element | None, ruta: str, nombre: str) -> str | None:
    if nodo is None:
        return None
    encontrado = nodo.find(ruta, NS)
    return encontrado.get(nombre) if encontrado is not None else None


def _notas(raiz: Element) -> dict[str, str]:
    """Las cbc:Note del perfil SPD, indexadas por su languageLocaleID.

    Ahi es donde EPM pone el contrato, el ciclo de corte y la cuota de
    financiacion: datos que el estandar no tiene donde colocar y que el emisor
    cuelga de una nota etiquetada.
    """
    notas: dict[str, str] = {}
    for nota in raiz.findall("cbc:Note", NS):
        etiqueta = nota.get("languageLocaleID")
        if etiqueta and nota.text:
            notas[etiqueta] = nota.text.strip()
    return notas


def _descuentos(raiz: Element) -> list[dict[str, Any]]:
    """Los AllowanceCharge de cabecera: subsidios, minimo vital, recargos."""
    salida: list[dict[str, Any]] = []
    for cargo in raiz.findall("cac:AllowanceCharge", NS):
        salida.append(
            {
                "id": _texto(cargo, "cbc:ID"),
                "es_recargo": _texto(cargo, "cbc:ChargeIndicator") == "true",
                "codigo_razon": _texto(cargo, "cbc:AllowanceChargeReasonCode"),
                "razon": _texto(cargo, "cbc:AllowanceChargeReason"),
                "porcentaje": _dinero(cargo, "cbc:MultiplierFactorNumeric"),
                "importe": _dinero(cargo, "cbc:Amount"),
                "base": _dinero(cargo, "cbc:BaseAmount"),
            }
        )
    return salida


def _linea(nodo: Element) -> InvoiceLine:
    return InvoiceLine(
        descripcion=_texto(nodo, "cac:Item/cbc:Description"),
        cantidad=_dinero(nodo, "cbc:InvoicedQuantity"),
        precio_unitario=_dinero(nodo, "cac:Price/cbc:PriceAmount"),
        importe=_dinero(nodo, "cbc:LineExtensionAmount"),
        codigo=_texto(nodo, "cac:Item/cac:StandardItemIdentification/cbc:ID"),
        extras={
            "unidad": _atributo(nodo, "cbc:InvoicedQuantity", "unitCode"),
            "cuenta": _texto(nodo, "cbc:AccountingCostCode"),
        },
    )


def parsear(xml: str) -> Invoice:
    """Mapea un Invoice UBL 2.1 al contrato. Lo que no esta, no esta."""
    raiz = fromstring(xml)

    if not raiz.tag.endswith("}Invoice") and raiz.tag != "Invoice":
        raise NoEsUnaFactura(f"la raiz es {raiz.tag}, no un Invoice")

    proveedor = raiz.find("cac:AccountingSupplierParty/cac:Party", NS)
    cliente = raiz.find("cac:AccountingCustomerParty/cac:Party", NS)
    totales = raiz.find("cac:LegalMonetaryTotal", NS)

    return Invoice(
        numero_factura=_texto(raiz, "cbc:ID"),
        cufe=_texto(raiz, "cbc:UUID"),
        fecha_emision=_fecha(raiz, "cbc:IssueDate"),
        fecha_vencimiento=_fecha(raiz, "cac:PaymentMeans/cbc:PaymentDueDate"),
        proveedor_nombre=_texto(proveedor, "cac:PartyLegalEntity/cbc:RegistrationName"),
        proveedor_id_fiscal=_texto(proveedor, "cac:PartyLegalEntity/cbc:CompanyID"),
        cliente_nombre=_texto(cliente, "cac:PartyLegalEntity/cbc:RegistrationName"),
        cliente_id_fiscal=_texto(cliente, "cac:PartyLegalEntity/cbc:CompanyID"),
        moneda=_texto(raiz, "cbc:DocumentCurrencyCode"),
        subtotal=_dinero(totales, "cbc:LineExtensionAmount"),
        impuesto_total=_dinero(raiz, "cac:TaxTotal/cbc:TaxAmount"),
        # TaxInclusiveAmount y no PayableAmount: lo pagadero resta descuentos y
        # meterlo aqui convertiria cada subsidio en un descuadre falso. Ver el
        # contrato, seccion "Coherencia".
        total=_dinero(totales, "cbc:TaxInclusiveAmount"),
        lineas=[_linea(n) for n in raiz.findall("cac:InvoiceLine", NS)],
        extras={
            "ubl_customization_id": _texto(raiz, "cbc:CustomizationID"),
            "ubl_profile_id": _texto(raiz, "cbc:ProfileID"),
            "ubl_invoice_type_code": _texto(raiz, "cbc:InvoiceTypeCode"),
            "ubl_tax_exclusive_amount": _dinero(totales, "cbc:TaxExclusiveAmount"),
            "ubl_payable_amount": _dinero(totales, "cbc:PayableAmount"),
            "ubl_allowance_total": _dinero(totales, "cbc:AllowanceTotalAmount"),
            "ubl_charge_total": _dinero(totales, "cbc:ChargeTotalAmount"),
            "ubl_prepaid_amount": _dinero(totales, "cbc:PrepaidAmount"),
            "notas": _notas(raiz),
            "descuentos": _descuentos(raiz),
        },
    )


def leer(ruta: Path) -> Invoice:
    """El camino completo: ZIP o XML en disco -> contrato."""
    return parsear(desanidar(localizar_xml(Path(ruta))))
```

- [ ] **Step 4: Correr y quedar verde**

Run: `pytest tests/test_parser.py -v`
Expected: `14 passed`

- [ ] **Step 5: Correr la suite entera y los verificadores**

Run:

```bash
pytest
ruff check src tests
mypy src
```

Expected: todo verde. Si `mypy --strict` se queja de `defusedxml` por falta de stubs, añadir a `pyproject.toml`:

```toml
[[tool.mypy.overrides]]
module = "defusedxml.*"
ignore_missing_imports = true
```

- [ ] **Step 6: Commit**

```bash
git add src/ubl_star/parser.py tests/test_parser.py pyproject.toml
git commit -m "feat: UBL 2.1 parser, each field anchored to its standard path (closes #3)"
```

---

### Task 6: Contra la factura real, fuera del repo

El parser está probado contra una fixture sintética. Antes de dar por buena la tarea hay que verlo leer una factura de verdad — y eso se hace **fuera del repo**, sin copiar nada dentro.

**Files:** ninguno del repo. Solo se ejecuta.

**Interfaces:**
- Consumes: `ubl_star.parser.leer`.
- Produces: nada versionado.

- [ ] **Step 1: Leer una factura real desde su carpeta privada**

La ruta de la factura **no se escribe en este documento**: se pasa por variable de
entorno. Un plan versionado en un repo público no lleva la ruta ni los valores de
la factura de nadie — ese es el mismo criterio que las fixtures sintéticas, un
escalón más arriba.

Run (desde `E:\MIS-REPO\ubl-star`, con el venv activo), apuntando `FACTURA` al ZIP
real que se quiera probar:

```bash
FACTURA="<ruta al zip del adjunto>" python -c "
import os
from ubl_star.parser import leer
f = leer(os.environ['FACTURA'])
print('lineas:', len(f.lineas))
print('cuadra:', f.cuadra(), f.problemas())
print('campos vacios:', [k for k, v in f.model_dump().items() if v is None])
"
```

Expected: `cuadra: True []`, un número de líneas mayor que cero, y en `campos
vacios` solo lo que el perfil SPD realmente no trae (`orden_compra`).

El criterio de éxito es **estructural, no de valores**: que la factura cuadre
consigo misma, que las líneas se hayan leído y que los huecos sean los esperados.
Ningún importe, número de factura ni fecha real se transcribe aquí ni al PR.

- [ ] **Step 2: Confirmar que nada real entró al repo**

Run:

```bash
git status --short
```

Expected: sin cambios. Si aparece cualquier `.xml`, `.zip` o `.pdf`, **borrarlo** — el hook lo bloquearía en el commit, pero no debe llegar ahí.

- [ ] **Step 3: Abrir la rama, el PR y pedir review**

```bash
git checkout -b feat/lector-ubl
git push -u origin feat/lector-ubl
gh pr create --title "feat: lector UBL 2.1 — ZIP, parser y contrato de salida" --body "Cierra #4, #3 y #2.

Tres piezas: \`zip.py\` localiza el XML dentro del adjunto DIAN, \`parser.py\` desanida el Invoice embebido en CDATA y lo mapea campo por campo, y \`schema/\` declara el contrato anclado a \`docs/contrato/factura-v1.md\` por un test de conformidad.

Fixtures sintéticas generadas por código; el hook \`.githooks/pre-commit\` bloquea cualquier documento fuera de \`tests/fixtures/\`.

@claude review

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

Nota: el push usa el token personal según la regla del repo:

```powershell
$token = [System.Environment]::GetEnvironmentVariable("GITHUB_TOKEN_PERSONAL", "User")
git -c "url.https://$token@github.com/.insteadOf=https://github.com/" push -u origin feat/lector-ubl
```

- [ ] **Step 4: Cerrar las issues al mergear**

El PR las cierra solo por los `closes #N`. Verificar tras el merge:

```bash
gh issue list -R CSalcedoDataBI/ubl-star --state open
```

Expected: quedan abiertas solo #5, #6 y #7.

---

## Self-review

**Cobertura del spec.** La capa 1 del spec (`ubl-star`, issues #4/#3/#2) queda cubierta: contrato en Task 2, fixture sintética en Task 3, ZIP en Task 4, parser en Task 5, verificación contra la factura real en Task 6. El scaffold y el hook (Task 1) no estaban explícitos en el spec pero los exige su sección de privacidad. Fuera de alcance por decisión del spec: #5 (fixtures PEPPOL), #6 (CLI a Parquet), #7 (CI).

**Placeholders.** Ninguno: cada paso lleva el código o el comando literal.

**Consistencia de tipos.** `Invoice`/`InvoiceLine`/`Dinero`/`Problema` se definen en Task 2 y se usan con esos mismos nombres en Task 5. `localizar_xml` se define en Task 4 y se importa en Task 5 con esa firma. `desanidar`/`parsear`/`leer` se declaran en el bloque de interfaces de Task 5 y se implementan con esas firmas.
