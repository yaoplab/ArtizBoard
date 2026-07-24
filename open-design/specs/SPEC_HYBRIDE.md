# ArtizBoard Staff — Spécifications Hybride (Restaurant + Boutique)

## Objectif
Gérer un établissement qui fait à la fois restaurant ET boutique (ex: restaurant qui vend ses vins, épices, livres de cuisine, t-shirts, ou boutique avec un coin café/restauration).

## Principe fondamental
**Même interface, comportement différent selon le type de produit.**

Le serveur/vendeur ne change pas d'app — c'est le produit qui détermine le flux :
- **Plat** (catégorie restaurant) → va en cuisine (KDS), stock ignoré
- **Produit** (catégorie boutique) → décrémente le stock, pas de cuisine

## Exemple concret
```
Restaurant "La République" vend aussi :
- Bouteilles de vin de sa cave → produit boutique (stock: 24)
- Sauce piment maison → produit boutique (stock: 50)
- T-shirts "La République" → produit boutique (stock: 15)
- Livre de recettes → produit boutique (stock: 8)
```

Un client peut commander :
- Un plat (passe par la cuisine) + une bouteille de vin (prise en stock directe)
- Que des produits boutique (pas de cuisine)
- Que des plats (pas de stock)

## Comment ça marche

### Au niveau du produit
Chaque produit a un indicateur `categorie.type` implicite via sa catégorie :

| Catégorie | Type implicite | Règle |
|---|---|---|
| Entrées, Plats, Grillades, Desserts | **Restaurant** | Pas de stock, passe par KDS |
| Boissons (servies en salle) | **Restaurant** | Pas de stock, passe par KDS |
| Vins, Épices, Textiles, Livres | **Boutique** | Stock géré, pas de cuisine |
| Boissons (bouteilles à emporter) | **Boutique** | Stock géré, pas de cuisine |

### Au niveau de la commande
Une commande peut contenir les deux types de produits :
```
Commande T1 :
  Riz au Gras    1×5 000 F  → Cuisine
  Poulet Braisé  1×6 000 F  → Cuisine
  Vin Rouge      1×8 000 F  → Stock (décrémenté)
  T-shirt        2×5 000 F  → Stock (décrémenté)
  Total : 29 000 F
```

### Workflow hybride

```
Client arrive → Table T1
    │
    ▼
PRENDRE COMMANDE (même écran que Restaurant)
  ├─ Le serveur ajoute des plats ET/OU des produits
  └─ Valider → la commande est créée
        │
        ├─ Partie Restaurant : envoyée en cuisine (en_attente)
        │   └─ KDS : en_attente → en_preparation → pret
        │
        └─ Partie Boutique : stock décrémenté immédiatement
            └─ Le serveur va chercher les produits en rayon
    │
    ▼
SERVIR
  ├─ Plats : le serveur apporte quand "pret"
  └─ Produits : déjà avec le serveur (pris au moment de la validation)
    │
    ▼
ENCAISSER (même écran que Restaurant)
  ├─ Un seul paiement pour toute la commande
  └─ Facture unique avec tous les articles
```

### Règle du stock
Pour les produits boutique dans une commande restaurant :
- **Option A (recommandé)** : le stock est réservé à la validation de la commande (décrémenté immédiatement). Si la commande est annulée, le stock est remboursé (mouvement: sortie_remboursement).
- **Option B** : le stock est décrémenté seulement au paiement. Risque : deux clients commandent le dernier article.

## Écrans

### Même écran "Commander" — le type de produit est visible
```
┌─────────────────────────────┐
│  Catégorie : Plats ▼        │
│  🍽 Riz au Gras    5 000 F │  ← icône cuisine
│  [+1] [0] [-1]             │
│                             │
│  Catégorie : Vins ▼         │
│  📦 Vin Rouge      8 000 F │  ← icône boutique
│  Stock: 24    [+1] [0] [-1]│
│  🛍 T-shirt        5 000 F │
│  Stock: 15    [+1] [1] [-1]│
│                             │
│  Panier : 3 articles 18 000 │
│  Table : T1                 │
│  [VALIDER]                  │
└─────────────────────────────┘
```

### Écran "En cours" — visibilité par table
```
┌─────────────────────────────┐
│  T1 — Sur place             │
│  🍽 Riz au Gras   1×5 000  │
│  🛍 T-shirt       1×5 000  │
│  Total 10 000 F  🟡 Cuisine │
│  [Servir quand tout prêt]   │
│  [Ajouter]                  │
└─────────────────────────────┘
```

### Écran "Stock boutique"
Le serveur/vendeur peut consulter le stock des produits boutique uniquement (pas les plats) :
```
┌─────────────────────────────┐
│  📦 Stock boutique          │
│  Vin Rouge      24          │
│  T-shirt        14 ⚠️       │
│  Sauce Piment   50          │
│  Livre Recettes  8          │
└─────────────────────────────┘
```

## Règles
1. Une catégorie est soit "restaurant" soit "boutique". Pas de mix au sein d'une catégorie.
2. Le produit hérite du type de sa catégorie.
3. Le KDS n'affiche que les produits de type restaurant.
4. Le stock n'est suivi que pour les produits de type boutique.
5. L'encaissement est unique par commande, quel que soit le mix restaurant/boutique.
6. La facture liste tous les articles (restaurant + boutique).
