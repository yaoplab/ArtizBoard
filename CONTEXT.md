# ArtizBoard — Contexte Projet (v2.0)

## Vue d'ensemble

ArtizBoard est un **système commercial hybride** (Boutique & Restaurant) conçu pour les petits commerces et restaurants en Afrique de l'Ouest. Il suit une architecture **Local-First** : l'intranet local est l'autorité unique, Supabase Cloud est un miroir de sauvegarde et un relais pour le portail client public.

### Problématique métier
- Connexion internet instable → mode 100% intranet obligatoire
- Multi-utilisateurs en réseau local (téléphones, tablettes, PC) → PostgreSQL local + PgBouncer
- Paiements mobile money (TMoney, Flooz) → intégration via interface abstraite
- Usage événementiel (soirée) → 50+ clients simultanés sur le Wi-Fi local

---

## Principe Fondateur

> **L'intranet local est la source unique de vérité.**
> Toute configuration (établissement, utilisateurs, produits, permissions) est créée et gérée exclusivement en local. Supabase Cloud est un réplica secondaire, jamais une autorité concurrente.

**Conséquences sur la synchronisation :**
- **Montée** (Local → Cloud) : Unidirectionnelle en écriture pour les données de config. Ajout/Update poussé vers le cloud.
- **Descente** (Cloud → Local) : Concerne **uniquement** les commandes passées par les clients via le portail public internet.
- **Pas de conflit** possible sur les configs → pas besoin de merge complexe.
- Pour les commandes (seule donnée bidirectionnelle) : le `version` côté cloud est comparé au `version` local.

---

## Architecture globale

```
                   ┌──────────────────────────────────┐
                   │       Supabase (Cloud)            │
                   │  PostgreSQL + Auth + Storage      │
                   │  (miroir de sauvegarde)           │
                   └────────────┬─────────────────────┘
                                │ synchro toutes les 10s
                                │ (unidirectionnelle config ↑)
                                │ (commandes client ↓)
                   ┌────────────▼─────────────────────┐
                   │  SERVEUR LOCAL (LAN)              │
                   │  ┌──────────────────────────────┐ │
                   │  │ PostgreSQL                   │ │
                   │  │ PgBouncer (pool_size=25,     │ │
                   │  │   max_client_conn=150,       │ │
                   │  │   pool_mode=transaction)     │ │
                   │  ├──────────────────────────────┤ │
                   │  │ sync_service.py              │ │
                   │  │ invoice_generator.py         │ │
                   │  │ dashboard_manager.py         │ │
                   │  │ ArtizBoardCommon (DS)        │ │
                   │  ├──────────────────────────────┤ │
                   │  │ Nginx (reverse proxy)        │ │
                   │  │  ├─ /admin  → App Admin Flet │ │
                   │  │  ├─ /staff  → App Staff Flet │ │
                   │  │  └─ /       → Portail Client │ │
                   │  └──────────────────────────────┘ │
                   └────────────┬─────────────────────┘
                                │ Wi-Fi local
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
   Admin (PC/Tablette)   Staff (Téléphone)    Clients (Téléphone)
   Interface Flet        Saisie mobile        QR code → menu → commande

                               ═══════════

                   ┌──────────────────────────────────┐
                   │    HOSTINGER BUSINESS            │
                   │    WordPress + PHP/MySQL         │
                   │  ┌────────────────────────────┐  │
                   │  │ Thème ArtizBoard            │  │
                   │  │ + Supabase JS SDK (CDN)     │  │
                   │  └────────────────────────────┘  │
                   └────────────┬─────────────────────┘
                                │ Supabase REST API
                                │ (lecture produits, pages, FAQ)
                                ▼
                   ┌──────────────────────────────────┐
                   │       Supabase (Cloud)            │
                   │  (données, auth, storage)        │
                   └──────────────────────────────────┘
                                ▲
                                │ INSERT commandes web
                                │ depuis WordPress
                   ┌────────────┴─────────────────────┐
                   │    CLIENTS INTERNET               │
                   │    (depuis chez eux, mobile)      │
                   └──────────────────────────────────┘
```

---

## Stack Technique

| Couche | Technologie | Rôle |
|---|---|---|
| Cloud DB | **Supabase (PostgreSQL)** | Sauvegarde, Auth publique, Storage |
| Local DB | **PostgreSQL + PgBouncer** | Autorité unique, multi-connexions |
| Reverse Proxy | **Nginx** | Load balancing Flet, WebSocket, assets |
| Apps | **Python 3.10+ + Flet 0.86+** | UI Desktop/Web/Mobile |
| Auth Locale | **JWT signé localement + bcrypt** | Fallback offline |
| Auth Cloud | **Supabase Auth** | Portail client public |
| PDF | **ReportLab** | Factures et rapports |
| Impression | **ESC/POS (python-escpos)** | Tickets thermiques réseau |
| Design | **Material Design v3 + Fibonacci** | ArtizBoardCommon |

---

## Base de Données — Schéma Corrigé (v2)

### Règles globales
- **UUID v4** généré côté client pour toutes les PK
- **Soft delete** : toute table a `deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL` (jamais de CASCADE destructif)
- **Audit trail** : `created_by UUID`, `updated_by UUID` sur toutes les tables
- **Optimistic locking** : `version INTEGER DEFAULT 1` sur toutes les tables modifiables. UPDATE vérifie `WHERE version = X` et incrémente.
- `sync_status` ∈ {local, pending, synced} pour le tracking de réplication
- `updated_at` TIMESTAMP WITH TIME ZONE pour le merging temporel
- Les migrations sont gérées par `db/migrations/` + table `schema_version`

---

### Table 1 — etablissements
```sql
CREATE TABLE etablissements (
    id UUID PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    type VARCHAR(50) CHECK(type IN ('boutique_reelle','boutique_virtuelle','restaurant')) NOT NULL,

    -- Identité & Storytelling
    logo_url TEXT,
    historique TEXT,
    mission TEXT,
    photo_presentation_url TEXT,

    -- Contacts
    adresse TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    horaires JSONB,              -- {"lundi":"08h-22h",...}
    telephone VARCHAR(50),
    email VARCHAR(255),
    site_web VARCHAR(255),
    reseaux_sociaux JSONB,       -- {"facebook":"...","instagram":"..."}

    -- Conditions de vente
    politique_retour TEXT,
    conditions_livraison TEXT,
    moyens_paiement_acceptes TEXT,
    taux_tva_defaut NUMERIC(4,2) DEFAULT 0,

    -- Audit
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);
```

### Table 2 — utilisateurs (Auth locale intégrée)
```sql
CREATE TABLE utilisateurs (
    id UUID PRIMARY KEY,                     -- = UID Supabase Auth si cloud
    etablissement_id UUID NOT NULL REFERENCES etablissements(id),
    nom VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    telephone VARCHAR(50),
    role_id UUID REFERENCES roles(id),

    -- Auth locale (mode intranet)
    password_hash TEXT,                      -- bcrypt
    refresh_token TEXT,
    refresh_token_expires_at TIMESTAMP WITH TIME ZONE,

    -- Device pairing
    device_id UUID,
    device_name VARCHAR(100),
    last_seen_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);
```

### Table 2b — rôles et permissions
```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    nom VARCHAR(50) UNIQUE NOT NULL,          -- admin, gerant, cuisinier, serveur, caissier
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local',
    version INTEGER DEFAULT 1
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL           -- create_order, manage_stock, view_dashboard, manage_establishment, print_invoice, manage_users, view_reports, process_payment, manage_faq, manage_categories
);

CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id),
    permission_id UUID REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);
```

### Table 3 — categories
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    icone VARCHAR(100),
    etablissement_id UUID NOT NULL REFERENCES etablissements(id),
    created_by UUID REFERENCES utilisateurs(id),
    updated_by UUID REFERENCES utilisateurs(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);
```

### Table 4 — produits
```sql
CREATE TABLE produits (
    id UUID PRIMARY KEY,
    categorie_id UUID NOT NULL REFERENCES categories(id),
    nom VARCHAR(255) NOT NULL,
    description TEXT,
    photo_url TEXT,
    prix NUMERIC(10,2) NOT NULL,
    taux_tva NUMERIC(4,2) DEFAULT 0,
    stock INTEGER DEFAULT 0,
    stock_alerte INTEGER DEFAULT 5,           -- seuil pour alerte rouge
    permets_commande BOOLEAN DEFAULT TRUE,
    etablissement_id UUID NOT NULL REFERENCES etablissements(id),
    created_by UUID REFERENCES utilisateurs(id),
    updated_by UUID REFERENCES utilisateurs(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);
```

### Table 5 — commandes
```sql
CREATE TABLE commandes (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES utilisateurs(id),
    staff_id UUID REFERENCES utilisateurs(id),
    etablissement_id UUID NOT NULL REFERENCES etablissements(id),

    -- Référence locale (pour clients de passage)
    reference_client VARCHAR(50),             -- "Table 12", "Comptoir", nom temporaire

    statut VARCHAR(50) CHECK(statut IN ('en_attente','en_preparation','pret','livre','annule')) DEFAULT 'en_attente',
    type_service VARCHAR(20) CHECK(type_service IN ('sur_place','emporter','livraison')) DEFAULT 'sur_place',

    total NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    montant_tva NUMERIC(10,2) DEFAULT 0.00,

    moyen_paiement VARCHAR(50) CHECK(moyen_paiement IN ('cash','tmoney','flooz','mixte')),
    statut_paiement VARCHAR(50) CHECK(statut_paiement IN ('en_attente','paye','echoue','rembourse')) DEFAULT 'en_attente',
    transaction_id VARCHAR(100),              -- ID transaction TMoney/Flooz

    created_by UUID REFERENCES utilisateurs(id),
    updated_by UUID REFERENCES utilisateurs(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);
```

### Table 6 — lignes_commande
```sql
CREATE TABLE lignes_commande (
    id UUID PRIMARY KEY,
    commande_id UUID NOT NULL REFERENCES commandes(id),
    produit_id UUID NOT NULL REFERENCES produits(id),
    quantite INTEGER NOT NULL CHECK(quantite > 0),
    prix_unitaire NUMERIC(10,2) NOT NULL,
    taux_tva_applique NUMERIC(4,2) DEFAULT 0,
    commentaire TEXT,                         -- "Sans oignons", "Bien cuit"
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);
```

### Table 7 — mouvements_stock
```sql
CREATE TABLE mouvements_stock (
    id UUID PRIMARY KEY,
    produit_id UUID NOT NULL REFERENCES produits(id),
    commande_id UUID REFERENCES commandes(id),
    ligne_commande_id UUID REFERENCES lignes_commande(id),
    type_mouvement VARCHAR(50) CHECK(type_mouvement IN ('entree_appro','sortie_vente','sortie_perte','sortie_remboursement','ajustement')) NOT NULL,
    quantite INTEGER NOT NULL CHECK(quantite > 0),
    motif TEXT,
    created_by UUID REFERENCES utilisateurs(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);
```

### Table 8 — factures
```sql
CREATE TABLE factures (
    id UUID PRIMARY KEY,
    commande_id UUID UNIQUE NOT NULL REFERENCES commandes(id),
    type_facture VARCHAR(20) CHECK(type_facture IN ('facture','avoir')) DEFAULT 'facture',
    facture_parent_id UUID REFERENCES factures(id),   -- si avoir, référence la facture d'origine
    numero_facture VARCHAR(100) UNIQUE NOT NULL,
    date_emission TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    pdf_path_local TEXT,
    pdf_url_cloud TEXT,
    imprimee BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES utilisateurs(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);
```

### Table 9 — evaluations
```sql
CREATE TABLE evaluations (
    id UUID PRIMARY KEY,
    produit_id UUID NOT NULL REFERENCES produits(id),
    commande_id UUID REFERENCES commandes(id),
    client_id UUID NOT NULL REFERENCES utilisateurs(id),
    note INTEGER CHECK(note BETWEEN 1 AND 5) NOT NULL,
    commentaire TEXT,
    est_visible BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);
```

### Table 10 — faqs
```sql
CREATE TABLE faqs (
    id UUID PRIMARY KEY,
    etablissement_id UUID NOT NULL REFERENCES etablissements(id),
    question TEXT NOT NULL,
    reponse TEXT NOT NULL,
    ordre INTEGER DEFAULT 0,
    created_by UUID REFERENCES utilisateurs(id),
    updated_by UUID REFERENCES utilisateurs(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);
```

### Table 11 — activation_codes (appairage appareils)
```sql
CREATE TABLE activation_codes (
    id UUID PRIMARY KEY,
    code_hash TEXT NOT NULL,                   -- SHA-256 du code généré
    utilisateur_id UUID REFERENCES utilisateurs(id),
    cree_par UUID NOT NULL REFERENCES utilisateurs(id),
    tentative_count INTEGER DEFAULT 0,
    max_tentatives INTEGER DEFAULT 3,
    expire_le TIMESTAMP WITH TIME ZONE NOT NULL,  -- créé + 5 minutes
    utilise_le TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
);
```

### Table 12 — devices (appareils appairés)
```sql
CREATE TABLE devices (
    id UUID PRIMARY KEY,
    utilisateur_id UUID NOT NULL REFERENCES utilisateurs(id),
    device_name VARCHAR(100),
    device_ip VARCHAR(45),
    dernier_acces TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    est_revoque BOOLEAN DEFAULT FALSE,
    revoque_par UUID REFERENCES utilisateurs(id),
    revoque_le TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Table 13 — pages_etablissement (pages du site web)
```sql
CREATE TABLE pages_etablissement (
    id UUID PRIMARY KEY,
    etablissement_id UUID NOT NULL REFERENCES etablissements(id),
    numero_page INTEGER NOT NULL,
    titre VARCHAR(255) NOT NULL,
    contenu_html TEXT DEFAULT '',
    contenu_css TEXT DEFAULT '',
    est_active BOOLEAN DEFAULT TRUE,
    ordre INTEGER DEFAULT 0,
    created_by UUID REFERENCES utilisateurs(id),
    updated_by UUID REFERENCES utilisateurs(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local',
    version INTEGER DEFAULT 1
);
```

### Table 14 — theme_config (paramètres thème WordPress)
```sql
CREATE TABLE theme_config (
    id UUID PRIMARY KEY,
    etablissement_id UUID NOT NULL REFERENCES etablissements(id),
    theme_id VARCHAR(100) DEFAULT 'artizboard',
    primary_color VARCHAR(7) DEFAULT '#1565C0',
    secondary_color VARCHAR(7) DEFAULT '#00897B',
    accent_color VARCHAR(7) DEFAULT '#E65100',
    surface_color VARCHAR(7) DEFAULT '#F5F7FA',
    font_heading VARCHAR(100) DEFAULT 'Inter',
    font_body VARCHAR(100) DEFAULT 'Inter',
    hero_title VARCHAR(255),
    hero_subtitle TEXT,
    hero_button_text VARCHAR(100) DEFAULT 'Voir la carte',
    nav_menu_items JSONB,
    footer_text TEXT,
    custom_css TEXT DEFAULT '',
    custom_js TEXT DEFAULT '',
    seo_title_template VARCHAR(255),
    seo_description TEXT,
    facebook_url VARCHAR(255),
    instagram_url VARCHAR(255),
    whatsapp_number VARCHAR(50),
    est_actif BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES utilisateurs(id),
    updated_by UUID REFERENCES utilisateurs(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local',
    version INTEGER DEFAULT 1
);
```

### Table 15 — schema_version (migrations)
```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    checksum VARCHAR(64),
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(100)
);
```

### Table 16 — backups (suivi des sauvegardes)
```sql
CREATE TABLE backups (
    id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    taille_bytes BIGINT,
    type VARCHAR(20) CHECK(type IN ('manuel','auto_hebdo','auto_mensuel')),
    encrypte BOOLEAN DEFAULT FALSE,
    local_path TEXT,
    external_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP WITH TIME ZONE
);
```

---

## Modules Fonctionnels

### 1. sync_service.py — Moteur de Synchronisation

**Rôle** : Service asynchrone en tâche de fond sur le serveur local.

**Principes** :
- Ping `https://xxx.supabase.co/rest/v1/` toutes les 10 secondes (HEAD request)
- **Montée (Local → Cloud)** : Pour toutes les tables sauf `commandes`, UPSERT unidirectionnel. `sync_status` : local → pending → synced.
- **Descente (Cloud → Local)** : Uniquement les `commandes` créées via le portail client public. Comparaison `version` pour détection de conflit.
- **Fichiers** : Upload async des PDFs factures, logos, images vers Supabase Storage.
- Mode 100% intranet : `sync_service.py` est désactivé (flag `sync_enabled=false` dans config.ini).

**Conflits** (commandes uniquement) : Si `version_cloud > version_local`, la version cloud est prioritaire (le client a déjà payé). Loggué dans `sync_conflicts` si nécessaire.

**PgBouncer** : Connexion via port 6432. Pool size = 25, max client connections = 150, pool mode = transaction.

---

### 2. invoice_generator.py — Factures PDF

**Déclenchement** : Automatique quand `statut IN ('pret','livre')` ET `statut_paiement = 'paye'`.

**Numéro facture** :
- Serveur accessible : `FAC-YYYYMMDD-XXXXX` via SEQUENCE PostgreSQL
- Appareil déconnecté : `FAC-YYYYMMDD-DEV{ID}-XXXXX` (renuméroté à la synchro)

**Contenu dynamique** :
- En-tête : Logo, nom établissement, adresse, téléphone (extrait de `etablissements`)
- Corps : Tableau des lignes (nom, qté, PU, TVA), total HT, total TVA, total TTC
- Bas de page : Moyen de paiement, statut, mission de l'entreprise, remerciements
- Note de crédit (avoir) : Si `type_facture = 'avoir'`, référence la facture d'origine

**Impression** : Via `python-escpos` en ESC/POS réseau. Le staff lance l'impression depuis son téléphone → le serveur local envoie les bytes à l'imprimante thermique.

---

### 3. dashboard_manager.py — Dashboard & Export

**KPIs** (période filtrée par dates) :
- CA global cumulé, panier moyen, nombre de commandes
- Répartition graphique des paiements (Cash, TMoney, Flooz)
- Évolution journalière du CA

**Boutique (Physique & Virtuelle)** :
- Mouvements de stock (approvisionnements, pertes, ventes)
- Alerte de rupture : `stock <= stock_alerte` (liste rouge)
- CA par catégorie de produit

**Restaurant** :
- Volume total plats vendus (cumul `lignes_commande`)
- Best-sellers Top 5 et Flops Top 5
- Répartition sur place / emporter / livraison

**Export CSV** (2 fichiers) :
- `journal_financier_YYYYMMDD.csv` : Date, ID Commande, Type établissement, Montant TTC, TVA, Moyen de paiement
- `journal_flux_YYYYMMDD.csv` : Date, Produit, Type flux, Quantité

**Export PDF** : Rapport synthétique avec KPIs, graphiques, résumé des ventes (via ReportLab).

---

### 4. App Admin (Flet) — Utilisateur Type 1

- **Identité marque** : Formulaire profil établissement (logo, historique, mission, contacts)
- **Logo** : stocké dans `uploads/logo/logo.png` — accessible via `http://127.0.0.1:8080/uploads/logo/logo.png`
- **Sélecteur mode** : Boutique Réelle / Virtuelle / Restaurant → modifie l'UI des autres apps
- **Catalogue & Stocks** : CRUD produits, saisie approvisionnements, gestion pertes
- **Utilisateurs & Rôles** : CRUD utilisateurs, attribution rôles, génération codes d'activation
- **Gestion appareils** : Liste des devices appairés, révocation
- **Dashboard** : KPIs, graphiques, exports CSV/PDF
- **Backup** : Lancer backup manuel, restaurer, télécharger sur USB
- **Configuration** : PgBouncer, sync enabled/disabled, paramètres réseau

---

### 5. App Staff (Flet) — Utilisateur Type 2 (Mobile-first)

- **Saisie commande mobile** : Composition panier en salle/rayon, validation immédiate
- **KDS Kanban** : Colonnes en_attente → en_preparation → pret → livré
- **Caisse POS tactile** : Encaissement cash/TMoney/Flooz, enregistrement auto des mouvements stock
- **Impression** : Bouton imprimer ticket thermique (via invoice_generator)
- **Notifications** : Polling 2s + alerte sonore sur nouvelles commandes
- **QR code table** : Scanner le QR code d'une table pour initier une commande associée

---

### 6. Portail Client (Flet) — Utilisateur Type 3 — Mode Local

- **Vitrine catalogue** : Navigation produits par catégorie, photos, descriptions, prix
- **Section "À Propos"** : Pages établissement, FAQ, commandes récentes
- **Panier & Commande** : Sélection, validation, choix sur place / emporter
- **Paiement** : Interface `PaymentGateway` → simulation USSD ou vraie intégration TMoney/Flooz
- **Mes commandes** : Suivi statut en temps réel (polling)
- **Factures** : Téléchargement PDF, historique des achats
- **Avis** : Notation (1-5 étoiles) et commentaires sur les produits commandés

**Mode Soirée Intranet** :
- QR code sur chaque table → `http://192.168.1.X:8080/?table=T12`
- Le client scanne → menu → commande (taggué `reference_client = 'T12'`)
- Option Captive Portal WiFi pour redirection automatique (routeurs compatibles)
- Sans Captive Portal : QR code imprimé suffit, zéro config réseau

### 7. Site Web Public (WordPress + Supabase) — Hébergé sur Hostinger

**Spécification détaillée** : `open-design/specs/SPEC_SITE_WEB.md`
**Skill technique** : `open-design/skills/wordpress-theme/SKILL.md`

- **WordPress** sur Hostinger Business (PHP/MySQL)
- **Thème custom ArtizBoard** avec templates appelant Supabase JS SDK
- **Données dynamiques** (produits, pages, FAQ, contact) → lues depuis Supabase REST API
- **Données statiques** (accueil, blog, CGV) → éditées dans WordPress admin
- **Panier** : localStorage côté client
- **Commande** : INSERT direct dans Supabase (puis sync → local pour la cuisine)
- **Pas de Python requis** — tout fonctionne en PHP/JS sur Hostinger

**Pages du site WordPress :**
- Accueil (éditable dans WordPress)
- Carte/Menu (template custom → Supabase)
- À Propos (template custom → pages_etablissement depuis Supabase)
- Contact (template custom → etablissements depuis Supabase)
- Blog/Actualités (WordPress standard)
- Pages légales (WordPress standard)

**Flux :**
```
Admin local → PostgreSQL → sync_service → Supabase Cloud
                                                │
                         WordPress (Hostinger) ←┘ (Supabase JS)
```

---

## Authentification & Sécurité Offline

### Appairage par QR code / Code activation

```
Admin (PC local)
  │
  ├─[1]─► Génère activation_code (secrets.token_hex(8) = 16 car. hex)
  │       Stocke code_hash = SHA-256(code) dans activation_codes
  │       Affiche le QR code à l'écran :
  │         http://192.168.1.X:8080/activate?token=abc...&device=TabletteCuisine
  │
Staff (téléphone)
  │
  ├─[2]─► Ouvre l'app ArtizBoard → scanne le QR code
  │       (ou saisit manuellement le code si pas de caméra)
  │
  ├─[3]─► L'app envoie token + device_info au POST /api/activate
  │
Serveur Local
  │
  ├─[4]─► Vérifie SHA-256(token) == code_hash
  │       Vérifie non expiré (5 min), tentative_count < max_tentatives
  │       Si OK → génère JWT signé localement (clé secrète dans config.ini)
  │       Enregistre l'appareil dans devices (device_name, IP)
  │       Répond : { access_token, refresh_token, user_info }
  │
  ▼
Appareil appairé, staff connecté
```

**Sécurité** :
- Token 16 caractères hex = 64 bits d'entropie
- 3 tentatives max, délai progressif (5s, 15s, 60s) après échecs
- Hashé SHA-256 en base (irréversible)
- L'admin peut révoquer un appareil à tout moment (flag `est_revoque`)

### Auth locale (mode 100% intranet)

Quand Supabase Auth est indisponible, le serveur local gère l'authentification :
- `utilisateurs.password_hash` (bcrypt) + `password_salt`
- JWT signé avec clé secrète locale (`SECRET_KEY` dans config.ini)
- Refresh token pour rotation sans re-saisie
- Fallback automatique : si `SUPABASE_URL` injoignable → auth locale

---

## Sauvegarde & Restauration

### Script de backup
- **Fréquence** : Hebdomadaire automatique (cron/Windows Task Scheduler)
- **Commande** : `pg_dump -h localhost -p 6432 -U artizboard -d artizboard_local | gzip | openssl enc -aes-256-cbc -pass pass:${BACKUP_PASSPHRASE} -out backup_YYYYMMDD.sql.gz.enc`
- **Checksum** : `sha256sum backup.sql.gz.enc > backup.sql.gz.enc.sha256`
- **Rétention 4-4-1** : 4 backups hebdo, 4 mensuels, 1 annuel

### Interface de restauration (Admin)
- Téléverser un fichier de backup
- Vérification checksum automatique avant import
- Restauration dans une base temporaire → validation → switch si OK
- Export sur support externe (USB/Disque dur)

### Suivi
- Table `backups` enregistre chaque backup : filename, checksum, taille, date
- Test de restauration automatisé mensuel sur base temporaire

---

## Paiement Mobile — Interface Abstraite

```python
from abc import ABC, abstractmethod
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

@dataclass
class PaymentResult:
    success: bool
    transaction_id: str
    status: PaymentStatus
    message: str

class PaymentGateway(ABC):
    @abstractmethod
    def request_payment(self, amount: Decimal, phone: str, reference: str) -> PaymentResult: ...
    @abstractmethod
    def check_status(self, transaction_id: str) -> PaymentStatus: ...

class SimulatedGateway(PaymentGateway): ...   # Dev/Test
class TMoneyGateway(PaymentGateway): ...      # Prod TMoney
class FloozGateway(PaymentGateway): ...       # Prod Flooz
```

---

## Flet — Configuration Déploiement

### Modes de fenêtre
- **Login** : 1100 × 680 px (ratio φ), fenêtre fixe, non redimensionnable, centrée
- **Dashboard** : Plein écran, maximisée, redimensionnable

### Développement local
```bash
python -m apps.admin     # App Admin
python run_admin.py      # Alternative (entry point pour flet pack)
```

### Desktop autonome
```bash
cd build
build_admin_desktop.bat  # → dist/ArtizBoard Admin.exe
```
`flet pack` (PyInstaller) empaquette Python + dépendances en un .exe autonome.
Les dépendances supplémentaires sont passées via `--add-data`.

### Mode production web
- Flet app en mode Web : `ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080)`
- Nginx en reverse proxy devant les apps Flet pour :
  - Gérer les connexions WebSocket (50+ simultanées)
  - Servir les assets statiques
  - SSL/TLS si exposé
- PgBouncer en mode `transaction`, `pool_size=25`, `max_client_conn=150`

### Test de charge
- Simuler 50 → 100 clients simultanés avant mise en production
- Vérifier : temps de réponse < 500ms, pas de timeouts PgBouncer

---

## Conventions Générales

- **Langue** : Code en anglais, UI en français, documentation en français
- **UUID v4** : `import uuid; uuid.uuid4()` pour tous les IDs
- **Design System** : `from ArtizBoardCommon import ds; ds.p.primary`, etc.
- **Zéro hardcoding** : Couleurs, espacements, tailles via `ds.*`
- **Soft delete** : Jamais de CASCADE destructif, utiliser `deleted_at`
- **Optimistic locking** : `WHERE version = X` sur chaque UPDATE
- **Paths** : `pathlib.Path`, jamais de chemins en dur
- **Migrations** : Scripts numérotés dans `db/migrations/`, exécutés séquentiellement
- **Tests** : pytest dans `tests/`, mocker Supabase pour tests offline
- **Config** : `ArtizBoardCommon/config.ini` pour connexions DB, clés, flags

---

## Livrables (Feuille de route)

| Livrable | Description | Fichiers |
|---|---|---|
| **A** | BDD & Synchro | `db/init_pg_local.sql`, `db/init_supabase.sql`, `db/migrations/`, `sync_service.py`, config PgBouncer |
| **B** | Facturation | `invoice_generator.py` (ReportLab + ESC/POS) |
| **C** | Dashboard | `dashboard_manager.py` (KPIs, exports CSV/PDF) |
| **D** | App Admin | `apps/admin/` (profil, catalogue, users, dashboard, backup) |
| **E** | App Staff | `apps/staff/` (mobile, QR code, KDS, caisse) |
| **F** | Portail Client Local | `apps/client/` (Flet web local, QR mode soirée) |
| **G** | Site Web Public | `wp-content/themes/artizboard/` (WordPress + Supabase JS, Hostinger) |
| **H** | Templates Modernes | 10 presets `theme_config` (5 resto + 5 boutique) + sélecteur Admin |
| **I** | Documentation | 11 skills × 3 formats (MD + DOCX + Obsidian), `graphity.py` |
