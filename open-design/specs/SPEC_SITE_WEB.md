# ArtizBoard — Spécifications Site Web Public (WordPress + Supabase)

**Skill** : `open-design/skills/wordpress-theme/SKILL.md`
**Emplacement** : `wp-content/themes/artizboard/`
**URL production** : https://aristodetoonasi.com
**Statut** : ✅ Déployé

## Architecture

```
Admin ArtizBoard (local) → PostgreSQL local → sync_service → Supabase Cloud
                                                                  │
                                            WordPress (Hostinger) ←┘ (Supabase JS SDK)
```

## Objectif
Fournir un site web public accessible depuis internet pour :
- Présenter l'établissement (vitrine, SEO, Google)
- Permettre aux clients de consulter le menu/catalogue et commander **avant** de venir
- Afficher les pages d'information (À Propos, Contact) gérées depuis l'Admin ArtizBoard
- Fonctionner sur l'hébergement Hostinger Business (PHP/MySQL, pas de Python)

## Architecture

```
┌─────────────────────────────────────────┐
│         HOSTINGER BUSINESS              │
│         WordPress + PHP/MySQL           │
│  ┌──────────────────────────────────┐   │
│  │  Thème custom ArtizBoard          │   │
│  │  ├─ header.php                   │   │
│  │  ├─ template-carte.php           │   │
│  │  ├─ template-apropos.php         │   │
│  │  ├─ template-contact.php         │   │
│  │  └─ assets/js/supabase-bridge.js │   │
│  └──────────────────────────────────┘   │
│              │                           │
│              │ Supabase JS SDK (CDN)      │
│              ▼                           │
└─────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│           SUPABASE CLOUD                │
│  ├─ Auth publique (anon)                │
│  ├─ API REST (/rest/v1/)               │
│  ├─ Storage (images produits, logo)     │
│  └─ Realtime (suivi commande)           │
└─────────────────────────────────────────┘
               ▲
               │ sync_service.py (Local→Cloud)
┌─────────────────────────────────────────┐
│         SERVEUR LOCAL (LAN)             │
│  App Admin → remplit catalogue, pages   │
│  sync_service → pousse vers Supabase    │
└─────────────────────────────────────────┘
```

## Données dynamiques (source = Supabase)

| Contenu | Table Supabase | Mise à jour |
|---|---|---|
| Logo, nom, adresse, téléphone | `etablissements` | Admin ArtizBoard → sync → Supabase |
| Menu / Carte (catégories + produits) | `categories` + `produits` | Admin ArtizBoard → sync → Supabase |
| Pages établissement (HTML/CSS) | `pages_etablissement` | Admin ArtizBoard → sync → Supabase |
| FAQ | `faqs` | Admin ArtizBoard |
| Moyens de paiement | `etablissements.moyens_paiement_acceptes` | Admin ArtizBoard |
| Horaires | `etablissements.horaires` (JSONB) | Admin ArtizBoard |
| Commandes clients web | `commandes` (INSERT) | WordPress → Supabase direct |

## Données statiques (source = WordPress admin)

| Contenu | Géré par |
|---|---|
| Page d'accueil (hero, texte intro) | WordPress editor |
| Blog / Actualités | WordPress posts |
| Pages légales (CGV, mentions) | WordPress pages |
| SEO (meta, sitemap) | WordPress + Yoast/plugin SEO |
| Design global (couleurs, polices) | Thème custom CSS |

## Pages du site

### 1. Accueil (page WordPress classique)
- Hero section avec logo + nom établissement (depuis Supabase)
- Texte d'intro (WordPress editor)
- Bouton "Voir la carte" → template-carte.php
- Bouton "Commander en ligne" → template-carte.php
- Dernières actualités (WordPress posts)

### 2. Carte / Menu (template-carte.php)
- Appelle Supabase `/rest/v1/categories` + `/rest/v1/produits`
- Affiche les catégories puis les produits avec prix
- Ajout au panier (localStorage)
- Panier flottant avec total et bouton commander
- Validation → INSERT dans Supabase `/rest/v1/commandes` + `/rest/v1/lignes_commande`
- Mode QR table : détection `?table=T12` dans l'URL → pré-remplit `reference_client`

### 3. À Propos (template-apropos.php)
- Appelle Supabase `/rest/v1/pages_etablissement?est_active=eq.true`
- Affiche les pages avec sous-navigation (onglets si plusieurs pages)
- Rendu HTML des pages (le contenu HTML/CSS de `pages_etablissement`)
- Section FAQ après les pages (depuis `/rest/v1/faqs`)

### 4. Contact (template-contact.php)
- Infos établissement depuis Supabase `/rest/v1/etablissements`
- Adresse, téléphone, email, site web
- Horaires (parsés depuis le JSONB)
- Moyens de paiement acceptés

### 5. Blog (WordPress standard)
- Articles, actualités, promotions
- Géré via l'admin WordPress

## Panier & Commande

### Panier (localStorage)
- Structure : `[{id_produit, nom, prix, quantite}]`
- Persiste entre les pages (SPA-like navigation)
- Badge compteur dans la navigation

### Commande (Supabase INSERT)
```
POST /rest/v1/commandes
{
  id: uuid(),
  etablissement_id: "...",
  reference_client: "Web" ou "T12" (si QR table),
  type_service: "sur_place" | "emporter" | "livraison",
  statut: "en_attente",
  statut_paiement: "en_attente",
  total: 15000,
  created_by: null  // client anonyme
}

POST /rest/v1/lignes_commande (pour chaque ligne)
{
  id: uuid(),
  commande_id: "...",
  produit_id: "...",
  quantite: 2,
  prix_unitaire: 5000
}
```

## Contraintes techniques
- **Hébergement** : Hostinger Business (PHP 8.x, MySQL, Apache/Nginx)
- **WordPress** : dernière version, thème custom minimal (pas de page builder lourd)
- **Supabase JS SDK** : chargé depuis CDN (`@supabase/supabase-js@2`)
- **Auth Supabase** : clé `anon` publique pour les lectures, `service_role` pour les écritures (via un proxy PHP simple ou via RLS configurée)
- **Cache** : pas de cache sur les pages dynamiques (carte, à propos) pour refléter les mises à jour en temps réel
- **Mobile-first** : responsive, optimisé téléphone (la majorité des clients consulteront sur mobile)
- **Pas de dépendance Python** : tout le code métier côté client est en JavaScript vanilla
- **Performances** : chargement initial < 3s, lazy loading des images Supabase Storage
- **Paiement** : pas intégré dans WordPress pour le MVP (paiement en salle ou à la livraison)

## WordPress — Structure du thème

```
wp-content/themes/artizboard/
├── style.css              # Thème header + CSS Design System
├── functions.php          # Enqueue scripts, menus, config
├── header.php             # Nav WordPress + badge panier
├── footer.php             # Footer + scripts inline
├── index.php              # Accueil (fallback)
├── page-accueil.php       # Template Accueil
├── template-carte.php     # Template Carte/Menu
├── template-apropos.php   # Template À Propos
├── template-contact.php   # Template Contact
├── single.php             # Article blog
├── assets/
│   ├── css/
│   │   └── theme.css      # Styles globaux
│   ├── js/
│   │   ├── config.js      # Supabase URL + anon_key
│   │   ├── api.js         # Wrapper Supabase (fetch fonctions)
│   │   ├── cart.js        # Gestion panier localStorage
│   │   └── app.js         # Composants dynamiques
│   └── img/
│       └── logo.png
└── inc/
    └── supabase-config.php # Stockage sécurisé des clés (pas dans le JS public)
```

## Design System CSS (rappel depuis DESIGN.md)

```css
:root {
  --primary: #1565C0;
  --primary-container: #BBDEFB;
  --surface: #F5F7FA;
  --error: #C62828;
  --success: #2E7D32;
  --text-strong: #1B1B1F;
  --text-soft: #455A64;
  --space-md: 20px; --space-lg: 32px;
  --shape-sm: 8px; --shape-md: 12px;
  --shape-full: 9999px;
  --font-body: 400 14px 'Inter';
  --font-title: 700 16px 'Inter';
}
```

## Flux de synchronisation

```
Admin ArtizBoard (local)
  │
  ├─ Modifie un produit, une catégorie, une page étab.
  │
  ▼
PostgreSQL local (autorité unique)
  │
  ├─ sync_service.py détecte le changement
  │   (sync_status: local → pending → synced)
  │
  ▼
Supabase Cloud (miroir)
  │
  ├─ API REST exposée (anon key, read-only pour les produits/pages)
  │
  ▼
WordPress (Hostinger)
  │
  └─ Supabase JS SDK lit les données → affiche le menu, pages, FAQ
     (pas de cache = toujours à jour)
```

## Règles

1. WordPress est le frontend public. Il ne stocke AUCUNE donnée métier (produits, commandes, pages étab.).
2. Toute donnée métier vient de Supabase, qui est un miroir du PostgreSQL local.
3. Le panier est stocké en localStorage (côté client uniquement).
4. Les commandes clients web sont envoyées directement à Supabase (INSERT avec anon key + RLS).
5. Le sync_service les redescend du cloud vers le local (pour que la cuisine voie les commandes web).
6. Aucune duplication de logique métier — si une règle change, elle change dans l'Admin Python uniquement.
