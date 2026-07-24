---
tags:
  - skill
  - test-generator
  - fonction
  - systeme-ferme
---

# Fonction Principale

Type: **systeme-ferme**

## 1. Fonction Principale



```
ENTRÉE                              →  TRAITEMENT                           →  SORTIE
Module/cible (admin|staff|client)      Créer classes TestXxx                   ├─ Fichier tests/test_xxx.py
Fixtures DB (conftest.py)              Méthodes test_* par fonctionnalité      ├─ pytest reports (CR)
                                       Assertions + edge cases                 └─ 100% pass ou skip motivé
```