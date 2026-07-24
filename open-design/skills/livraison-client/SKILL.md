# Skill: Livraison Client — Logiciel Tiers

## 0. Contexte

**Projet** : ArtizBoard (mais applicable à tout logiciel B2B local)
**Utilisateurs** : Prestataire (toi) → Client (restaurateur, boutiquier)
**Dépendances** : [[livrer.py]], [[wordpress-theme]], [[securite-audit]]
**Prérequis** : Client signé, matériel prêt (PC, téléphones, imprimante)

## 1. Fonction Principale

### Type : Système Fermé

```
ENTRÉE                              →  TRAITEMENT                           →  SORTIE
Client avec restaurant/boutique        Installation + configuration          ├─ Système opérationnel
Matériel : PC, téléphones, wifi        Formation 2h                          ├─ Client autonome
1 établissement à configurer           Remise documentation                  └─ Contrat signé
```

## 2. Contraintes Fonctionnelles

### Tableau global — Avant la livraison

| # | Contrainte |
|---|---|
| C1 | Le client doit avoir signé le contrat (prix, durée, services inclus) |
| C2 | Le matériel minimum est vérifié : 1 PC Windows, 1 téléphone Android, Wi-Fi local |
| C3 | La base de données est vierge ou pré-remplie avec les données du client |
| C4 | Un établissement est créé AVANT la livraison (nom, type, coordonnées) |
| C5 | Le site WordPress est configuré avec le nom de domaine du client |

### Tableau global — Pendant la livraison

| # | Contrainte |
|---|---|
| C6 | L'installation se fait SUR PLACE (restaurant/boutique du client) |
| C7 | Une sauvegarde initiale est faite immédiatement après configuration |
| C8 | La formation couvre : Admin (catalogue, users), Staff (commande, encaissement), Client (QR) |
| C9 | Le client réalise AU MOINS une commande complète (test réel) avant ton départ |
| C10 | Toutes les informations de connexion sont remises sur papier + email |

### Tableau global — Après la livraison

| # | Contrainte |
|---|---|
| C11 | Un suivi est programmé à J+7 (appel ou visite) |
| C12 | Le client a ton numéro WhatsApp pour les urgences |
| C13 | Les mises à jour sont communiquées par WhatsApp/email |
| C14 | Le premier mois est gratuit si convenu (période d'essai) |

### Sous-système A — Contrat client

| # | Contrainte |
|---|---|
| A1 | Le contrat précise : nom établissement, forfait choisi, prix/mois, durée min (3 mois) |
| A2 | Le contrat précise les services INCLUS (màj, support WhatsApp, sync) |
| A3 | Le contrat précise les services NON INCLUS (nouveau matériel, déplacement hors Lomé) |
| A4 | Une clause de résiliation : 1 mois de préavis, données exportables |

### Sous-système B — Documentation client (à remettre)

| # | Contrainte |
|---|---|
| B1 | Un guide Admin expliquant : ajouter/modifier des produits, gérer les utilisateurs |
| B2 | Un guide Staff expliquant : prendre commande, encaisser, voir la cuisine |
| B3 | Une fiche QR code : comment imprimer et coller les QR sur les tables |
| B4 | Une fiche "Que faire si..." : Wi-Fi coupé, appli bloquée, erreur connexion |
| B5 | Les identifiants de connexion : Admin (PC), Staff (QR code), Client (URL) |

### Sous-système C — Formation 2h

| # | Contrainte |
|---|---|
| C1 | 30 min : Admin (PC) — gérer son catalogue, ses utilisateurs, voir les rapports |
| C2 | 30 min : Staff (téléphone) — prendre une commande, encaisser, KDS |
| C3 | 30 min : Client (QR) — expliquer aux clients comment commander |
| C4 | 30 min : Questions + test réel (faire une commande complète) |

## 3. Kit de livraison physique

| Pièce | Format | Contenu |
|---|---|---|
| Contrat | Papier + PDF | 2 exemplaires signés |
| Fiche Admin | Papier A4 | Instructions gérant |
| Fiche Staff | Papier A4 | Instructions serveurs |
| Fiche QR | Papier A4 | Modèle à imprimer |
| Fiche Support | Papier A4 | Numéros, "Que faire si..." |
| Identifiants | Carte plastifiée | Login, mot de passe, URLs |
| QR codes tables | Stickers imprimés | 30 QR codes (T1→T30) |

## 4. Checklist avant livraison

- [ ] Contrat signé
- [ ] Base de données configurée (établissement, admin, quelques produits)
- [ ] Site WordPress en ligne (ou prévu)
- [ ] PC Windows prêt avec Admin.exe installé
- [ ] Téléphone Android avec Staff APK installé
- [ ] Imprimante thermique configurée (si demandé)
- [ ] QR codes imprimés et plastifiés
- [ ] Documentation imprimée en 2 exemplaires
- [ ] Sauvegarde initiale faite
- [ ] Test complet réalisé (commande → cuisine → encaissement)

## 5. Step by Step — Jour de livraison

| Heure | Action | Durée |
|---|---|---|
| 09:00 | Installation PC + test connexion DB + sync | 30 min |
| 09:30 | Configuration catalogue (avec le client) | 30 min |
| 10:00 | Installation téléphone + scan QR activation | 15 min |
| 10:15 | Formation Admin (catalogue, users, rapports) | 30 min |
| 10:45 | Formation Staff (commande, encaissement, KDS) | 30 min |
| 11:15 | Test réel : le client commande depuis son tel | 15 min |
| 11:30 | Questions / Réponses | 30 min |
| 12:00 | Signature PV de livraison + remise docs | 15 min |
| 12:15 | FIN | |

## 6. Deux exemples

### Exemple 1 — Livraison Restaurant (cas simple)

Client : "Chez Ama" — 8 tables, 2 serveurs, 1 gérante
Matériel : 1 PC portable (gérante), 2 téléphones (serveurs)
Forfait : Standard — 35 000 F/mois
Temps : 2h30

1. PC configuré avec Admin.exe + données saisies (12 plats)
2. 2 téléphones avec APK Staff + QR codes scannés
3. Formation gérante : modifier le menu, voir le CA
4. Formation serveurs : prendre commande, encaisser
5. Test : T1 → 2 plats → cuisine → encaissé → OK

### Exemple 2 — Livraison Boutique (cas complexe)

Client : "Boutique Élégance" — 200 produits, 1 vendeuse, 1 gérant
Matériel : 1 PC + 1 téléphone
Forfait : Boutique — 25 000 F/mois
Temps : 3h

1. Import des 200 produits via Admin (copier-coller depuis Excel)
2. Configuration des alertes stock (seuil 5 unités)
3. Formation vendeuse : vendre, encaisser, voir le stock
4. Test : vente de 3 articles → stock décrémenté → facture imprimée → OK

## Emplacement
- Skill : `open-design/skills/livraison-client/SKILL.md`
- Documentation client : `livraison-client/` (généré automatiquement)
