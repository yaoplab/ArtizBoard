# ArtizBoard Staff — Spécifications Boutique

## Objectif
Permettre à un vendeur/boutiquier de gérer les ventes, le stock et les encaissements — depuis un téléphone/tablette connecté au Wi-Fi local ou en itinérance dans le magasin.

## Différence fondamentale avec le Restaurant
- **Pas de tables.** Le client est un individu ou un "client au comptoir".
- **Pas de cuisine.** Pas de KDS, pas de préparation.
- **Stock critique.** Chaque vente décrémente le stock. Alerte si rupture.
- **Paiement immédiat.** Pas de "payer plus tard" — la marchandise ne sort pas sans paiement.
- **Encaissement direct.** Le vendeur encaisse au moment de la vente.

## Profil utilisateur
Vendeur/Boutiquier — debout ou derrière un comptoir. Peut se déplacer en rayon avec son téléphone pour renseigner un client ou vérifier un stock.

## Vocabulaire métier
- **Vente au comptoir** : client présent physiquement, paie immédiatement.
- **Vente en ligne** : client commande via le portail web, paie en ligne, vient retirer ou se fait livrer.
- **Rupture de stock** : `stock ≤ stock_alerte` → alerte rouge.
- **Approvisionnement** : entrée de stock.

## Contraintes techniques
- Téléphone/tablette en réseau Wi-Fi local (PostgreSQL)
- Flet 0.86+, Material Design v3 + Fibonacci
- Mise à jour du stock en temps réel (optimistic locking)

---

## Workflow vendeur

```
Client arrive au comptoir / en rayon
    │
    ▼
1. CHOISIR PRODUITS
   ├─ Écran : catalogue par catégorie
   ├─ Vendeur sélectionne les articles → ajoute au panier
   ├─ Le stock est vérifié : si insuffisant → message "Stock : 2 restants"
   ├─ Possibilité de scanner un code-barres (futur)
   └─ Valider le panier

2. PAYER (obligatoire, immédiat)
   ├─ Écran : montant total + choix du moyen de paiement
   ├─ Espèces : le vendeur saisit le montant reçu → calcul du rendu
   ├─ TMoney / Flooz : simulation ou intégration réelle
   └─ Validation → stock décrémenté automatiquement (mouvement_stock: sortie_vente)

3. FACTURE
   ├─ Générée automatiquement (PDF)
   ├─ Imprimable (ticket thermique)
   └─ Remise au client

4. SUIVI STOCK
   ├─ Le vendeur voit les alertes de rupture
   ├─ Peut enregistrer un approvisionnement
   └─ Peut déclarer une perte (casse, vol)
```

## Statuts

| Statut commande | Signification |
|---|---|
| `livre` | Vente conclue (immédiat en boutique) |
| `annule` | Annulée avant paiement |

| Statut paiement | Signification |
|---|---|
| `paye` | Réglé (obligatoire pour valider la vente) |
| `rembourse` | Remboursé (avoir) |

## Types de mouvement de stock

| Type | Déclencheur |
|---|---|
| `sortie_vente` | Automatique à la validation du paiement |
| `entree_appro` | Saisie manuelle par le vendeur/admin |
| `sortie_perte` | Saisie manuelle (casse, vol, péremption) |
| `ajustement` | Correction d'inventaire |

## Écrans de l'app

### Écran 1 — Vendre
```
┌─────────────────────────────┐
│  Catégorie : Tissus ▼       │
│                             │
│  Pagne Wax          5 000 F │
│  Stock: 12    [+1] [0] [-1] │
│  Tissu Bazin        8 000 F │
│  Stock: 3 ⚠️ [+1] [1] [-1] │
│                             │
│  Panier : 2 articles 13 000 │
│  [VALIDER]                  │
└─────────────────────────────┘
```

### Écran 2 — Encaisser
```
┌─────────────────────────────┐
│  Total : 13 000 F           │
│                             │
│  [ESPÈCES] [TMONEY] [FLOOZ]│
│                             │
│  Montant reçu : [15 000]    │
│  Rendu        : 2 000 F     │
│                             │
│  [ENCAISSER ET CLÔTURER]   │
└─────────────────────────────┘
```

### Écran 3 — Stock
```
┌─────────────────────────────┐
│  ⚠️ Alertes                 │
│  Tissu Bazin — Stock: 3     │
│  Pagne Wax — Stock: 1       │
├─────────────────────────────┤
│  Derniers mouvements        │
│  15/07  Pagne Wax  -2 vente │
│  15/07  Bazin      +10 appr│
│  14/07  Wax        -1 perte │
├─────────────────────────────┤
│  [+ Approvisionnement]      │
│  [+ Déclarer une perte]     │
└─────────────────────────────┘
```

### Écran 4 — Mon CA
```
┌─────────────────────────────┐
│  Aujourd'hui                │
│  Espèces : 85 000 F         │
│  TMoney  : 23 000 F         │
│  Flooz   : 12 000 F         │
│  Total   : 120 000 F        │
│  Ventes  : 14               │
└─────────────────────────────┘
```

## Règles métier
1. Paiement immédiat obligatoire. Pas de "plus tard".
2. Le stock est décrémenté automatiquement à la validation du paiement.
3. Une vente ne peut pas être validée si le stock est insuffisant.
4. Le vendeur peut enregistrer des approvisionnements et des pertes.
5. Le ticket/facture est généré automatiquement à la validation.
