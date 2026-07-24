---
tags:
  - skill
  - test-generator
  - contrainte
  - sous-systeme
  - priorite-1
---

# Sous-système E: Test Invoice (fix skip)

- **E1**: `test_generate_invoice` doit passer avec la vraie DB et un mock PDF
- **E2**: `test_invoice_number_format` vérifie `FAC-YYYYMMDD-XXXXX`
- **E3**: `test_generate_avoir` vérifie la référence à la facture parent
- **E4**: Les tests ne créent pas de vrais fichiers — mock uniquement
