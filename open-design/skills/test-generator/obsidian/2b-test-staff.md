---
tags:
  - skill
  - test-generator
  - contrainte
  - sous-systeme
  - priorite-1
---

# Sous-système B: Test Staff

- **B1**: Tester la prise de commande : `_validate()` crée commandes + lignes_commande
- **B2**: Tester le panier : ajouter, retirer, vider
- **B3**: Tester le KDS : `_ch_kds` change le statut
- **B4**: Tester l'encaissement : `_payer` met à jour `statut_paiement = 'paye'`
- **B5**: Tester les tables : `_set_table`, `_tables`
- **B6**: Tester le CA serveur : requête agrégée par moyen de paiement
