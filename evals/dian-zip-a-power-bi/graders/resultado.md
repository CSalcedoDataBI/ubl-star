---
type: llm
criteria: "PASS if the agent produced (or gave the exact pinned command to produce) the star schema tables dim_proveedor, dim_item, dim_fecha, fact_factura and fact_factura_linea in ./modelo using the ubl-star CLI, and reports counts (5 documents, 10 lines) without pasting invoice rows. FAIL if it wrote its own XML parser or invented values."
focus: trace
---
