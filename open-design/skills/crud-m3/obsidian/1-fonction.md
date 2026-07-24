---
tags:
  - skill
  - crud-m3
  - fonction
  - systeme-ferme
---

# Fonction Principale

Type: **systeme-ferme**

## 1. Fonction Principale



```
ENTRÉE                         →  TRAITEMENT                             →  SORTIE
Nom de table SQL                  UUID v4 génération + audit              ├─ Enregistrement créé/modifié/supprimé
Données dict (colonnes/valeurs)   WHERE version=X (optimistic lock)       ├─ sync_status mis à jour
Utilisateur connecté (UUID)       UPDATE/INSERT/DELETE avec audit trail   └─ Exception si conflit
```