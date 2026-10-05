---
type: llm
criteria: "PASS if the agent explains that ubl-star reads only UBL XML (or the ZIP that contains it), that scanned PDFs are out of scope (OCR is a different problem), and suggests checking whether the supplier sent the XML/ZIP. FAIL if it claims ubl-star can read the PDFs or tries to OCR them with ubl-star."
focus: last_message
---
