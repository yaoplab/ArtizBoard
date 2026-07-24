---
tags:
  - skill
  - kds-kanban
  - contrainte
---

# Contraintes Fonctionnelles

## Tableau global

- **C1**: 3 colonnes fixes : **En attente** (tertiary), **En préparation** (primary), **Prêt** (success)
- **C2**: Chaque colonne a un header avec compteur (badge pilule)
- **C3**: Les commandes sont groupées par statut depuis la DB : `SELECT * WHERE statut IN ('en_attente','en_preparation','pret')`
- **C4**: Le bouton flèche (→) avance d'un statut : `en_attente → en_preparation → pret`
- **C5**: Chaque carte commande montre : ID table, temps écoulé, liste des plats, total, flèche
- **C6**: Le rafraîchissement est déclenché manuellement (bouton refresh) ou automatiquement (polling 10s)
- **C7**: La colonne a une bordure colorée gauche de 3px

## [[2a-rendu-du-kanban|Sous-système A: Rendu du kanban]]

## [[2b-avancement-de-commande|Sous-système B: Avancement de commande]]

## [[2c-fetch-des-lignes|Sous-système C: Fetch des lignes]]

