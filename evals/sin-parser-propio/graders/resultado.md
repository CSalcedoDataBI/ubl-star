---
type: llm
criteria: "PASS if the totals come from running the ubl-star CLI (fact_factura) rather than from parsing XML by hand, and the five documents are listed with their total and supplier (DEE00000001, NC00000001, ND00000001 with 30190 from SERVICIOS PUBLICOS EJEMPLO; INV-0001 and CN-0001 with 1210 from EXAMPLE SUPPLIER B.V.), indicating which are credit notes. FAIL if it parsed the XML itself or invented values."
focus: trace
---
