---
tags:
  - skill
  - kds-kanban
  - fonction
  - systeme-ferme
---

# Fonction Principale

Type: **systeme-ferme**

## 1. Fonction Principale



```
ENTRÉE                              →  TRAITEMENT                              →  SORTIE
commandes en_attente/en_prep/pret     3 colonnes kanban :                      ├─ Kanban rendu (Flet)
clic sur flèche → avancer            → en_attente → en_preparation → pret     └─ Statut mis à jour en DB
ID commande (UUID)                     UPDATE statut, refresh auto
```