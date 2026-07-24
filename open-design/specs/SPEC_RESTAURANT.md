# ArtizBoard Staff — Spécifications Restaurant

## Objectif
Permettre à un serveur de prendre des commandes en salle, les envoyer en cuisine, les servir, encaisser et clôturer — depuis un téléphone/tablette connecté au Wi-Fi local.

## Profil utilisateur
Serveur/Serveuse — debout, en mouvement, une main libre. Gère 4 à 10 tables simultanément. Encaissements en espèces, TMoney ou Flooz. Doit pouvoir voir son CA personnel en fin de service.

## Vocabulaire métier
- **Table** : emplacement physique (T1, T2...) ou "Terrasse 3", "Comptoir". Une commande = une table.
- **Service** : une commande peut être sur place, à emporter ou en livraison.
- **Clôture** : une commande est clôturée quand elle est livrée ET payée.

## Contraintes techniques
- Téléphone/tablette en réseau Wi-Fi local (PostgreSQL via PgBouncer)
- Flet 0.86+, Material Design v3 + Fibonacci
- Hors-ligne toléré : si Wi-Fi perdu, la commande est sauvegardée localement

---

## Workflow serveur

```
Arrivée client → attribution table (obligatoire)
    │
    ▼
1. PRENDRE COMMANDE
   ├─ Écran : liste des tables actives + bouton "Nouvelle commande"
   ├─ Serveur sélectionne la table (ou crée une nouvelle table)
   ├─ Parcourt les catégories → plats → ajoute au panier
   ├─ Choix : sur place / à emporter / livraison
   └─ Valider → commande créée (en_attente, non payée)

2. SUIVRE COMMANDES (vue "En cours")
   ├─ Écran : carte par table, avec statut visible
   │   T1 [4 plats • 12 500 F] 🟡 En cuisine
   │   T3 [2 plats • 6 000 F]  🟢 Prêt à servir
   │   T5 [vide]                ⚪ Libre
   ├─ Le serveur voit d'un coup d'œil ce qui est prêt à servir
   └─ Peut ajouter des articles à une commande existante

3. SERVIR
   └─ Le serveur voit "T3 = Prêt" → il apporte les plats → marque "livré"

4. ENCAISSER (vue "À encaisser")
   ├─ Écran : liste des commandes non payées (toutes tables confondues)
   │   T1 — 12 500 F — Pret — [💰 Encaisser]
   │   T4 — 8 000 F — Livré — [💰 Encaisser]
   ├─ Le serveur clique → choisit le moyen de paiement
   ├─ Paiement enregistré → commande clôturée
   └─ Facture PDF générée automatiquement + ticket thermique

5. MON CA (fin de service)
   ├─ Total encaissé par le serveur aujourd'hui
   ├─ Par moyen de paiement (espèces, TMoney, Flooz)
   └─ Permet de savoir combien d'espèces remettre en caisse
```

## Statuts

| Statut commande | Signification | Qui change |
|---|---|---|
| `en_attente` | Envoyée en cuisine | Serveur (automatique à la validation) |
| `en_preparation` | Le cuisinier prépare | Cuisinier (KDS) |
| `pret` | Prêt à servir | Cuisinier (KDS) |
| `livre` | Servi au client | Serveur |
| `annule` | Annulée | Serveur |

| Statut paiement | Signification | Qui change |
|---|---|---|
| `en_attente` | Pas encore payé | (défaut) |
| `paye` | Payé | Serveur (encaissement) |
| `rembourse` | Remboursé | Gérant/Admin |

## Écrans de l'app

### Écran 1 — Nouvelle commande
```
┌─────────────────────────────┐
│  Tables                     │
│  [T1 ●] [T2 ○] [T3 ○] ...  │
│  [+ Nouvelle table]         │
├─────────────────────────────┤
│  Catégorie : Entrées ▼      │
│                             │
│  Salade Béninoise   2 500 F │
│  [+1] [0] [-1]              │
│  Beignets Poisson    2 000 F│
│  [+1] [2] [-1]              │
│                             │
│  Panier : 3 articles 6 500 F│
│  Type : Sur place ▼         │
│  [VALIDER]                  │
└─────────────────────────────┘
```

### Écran 2 — En cours
```
┌─────────────────────────────┐
│  T1 — Sur place             │
│  Riz au Gras   1×5 000      │
│  Jus Bissap    2×1 500      │
│  Total 8 000 F  🟡 En cuisine│
│  [Ajouter] [Annuler]        │
├─────────────────────────────┤
│  T3 — Sur place             │
│  Poulet Braisé 1×6 000      │
│  Total 6 000 F  🟢 Prêt     │
│  [Servir ✓] [Ajouter]       │
├─────────────────────────────┤
│  [+ Nouvelle commande]      │
└─────────────────────────────┘
```

### Écran 3 — Encaisser
```
┌─────────────────────────────┐
│  À encaisser                │
├─────────────────────────────┤
│  T1 — 8 000 F — Pret        │
│  [💰 Encaisser]             │
├─────────────────────────────┤
│  T4 — 15 000 F — Livré      │
│  [💰 Encaisser]             │
├─────────────────────────────┤
│  Mon CA aujourd'hui         │
│  Espèces : 45 000 F         │
│  TMoney  : 12 000 F         │
│  Flooz   :  8 000 F         │
│  Total   : 65 000 F         │
└─────────────────────────────┘
```

### Écran 4 — Encaissement (dialog)
```
┌─────────────────────────────┐
│  T1 — 8 000 F               │
│                             │
│  [ESPÈCES]   8 000 F        │
│  [TMONEY]    8 000 F        │
│  [FLOOZ]     8 000 F        │
│                             │
│  Montant reçu : [8 000]     │
│  Rendu        : 0 F         │
│                             │
│  [VALIDER LE PAIEMENT]      │
└─────────────────────────────┘
```

## Règles métier
1. Une commande = une table (obligatoire, pas de commande orpheline)
2. Le serveur NE modifie PAS les statuts cuisine (sauf annulation)
3. La facture est générée quand `statut = livré` ET `statut_paiement = payé`
4. Le ticket thermique est imprimable via le serveur local
5. Le CA serveur est consultable en temps réel
6. Le serveur peut ajouter des articles à une commande existante tant qu'elle n'est pas clôturée
