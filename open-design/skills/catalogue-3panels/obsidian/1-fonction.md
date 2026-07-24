---
tags:
  - skill
  - catalogue-3panels
  - fonction
  - systeme-ferme
---

# Fonction Principale

Type: **systeme-ferme**

## 1. Fonction Principale



```
ENTRÉE                              →  TRAITEMENT                              →  SORTIE
catégories + produits (DB)            Layout : 3 panneaux en Row                ├─ Liste catégories (gauche)
produit sélectionné (click)           Refresh pattern (mounted/unmounted)        ├─ Liste produits filtrés (centre)
ec84fd08-...                          Dialog CRUD pour ajout/modif/suppr        └─ Détail produit (droite)
```