---
type: llm
criteria: "The synthetic fixtures contain COP documents (invoice 190 IVA, credit note 190, debit note 190) and EUR documents (invoice 210 IVA, credit note 210). PASS if the answer reports net IVA per currency, subtracting credit notes: COP 190 and EUR 0 (equivalent formatting accepted), and does not add COP and EUR together. FAIL if credit notes are added instead of subtracted, if currencies are mixed, or if the numbers are different."
focus: last_message
---
