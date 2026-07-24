-- =====================================================================
-- ArtizBoard — Schéma Supabase Cloud (v2)
-- Livrable A — init_supabase.sql
-- Ce script crée les tables miroir dans Supabase.
-- Les PK sont UUID générées par les clients locaux, pas d'auto-génération.
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================================
-- 1. ÉTABLISSEMENTS
-- =====================================================================
CREATE TABLE etablissements (
    id UUID PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    type VARCHAR(50) CHECK(type IN ('boutique_reelle','boutique_virtuelle','restaurant')) NOT NULL,
    logo_url TEXT,
    historique TEXT,
    mission TEXT,
    photo_presentation_url TEXT,
    adresse TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    horaires JSONB,
    telephone VARCHAR(50),
    email VARCHAR(255),
    site_web VARCHAR(255),
    reseaux_sociaux JSONB,
    politique_retour TEXT,
    conditions_livraison TEXT,
    moyens_paiement_acceptes TEXT,
    taux_tva_defaut NUMERIC(4,2) DEFAULT 0,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);

-- =====================================================================
-- 2. RÔLES ET PERMISSIONS
-- =====================================================================
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    nom VARCHAR(50) UNIQUE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- =====================================================================
-- 3. UTILISATEURS
-- =====================================================================
CREATE TABLE utilisateurs (
    id UUID PRIMARY KEY,
    etablissement_id UUID NOT NULL REFERENCES etablissements(id) ON DELETE CASCADE,
    nom VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    telephone VARCHAR(50),
    role_id UUID REFERENCES roles(id),
    password_hash TEXT,
    refresh_token TEXT,
    refresh_token_expires_at TIMESTAMP WITH TIME ZONE,
    device_id UUID,
    device_name VARCHAR(100),
    last_seen_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);

-- =====================================================================
-- 4. CATÉGORIES
-- =====================================================================
CREATE TABLE categories (
    id UUID PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    icone VARCHAR(100),
    etablissement_id UUID NOT NULL REFERENCES etablissements(id) ON DELETE CASCADE,
    created_by UUID REFERENCES utilisateurs(id),
    updated_by UUID REFERENCES utilisateurs(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);

-- =====================================================================
-- 5. PRODUITS
-- =====================================================================
CREATE TABLE produits (
    id UUID PRIMARY KEY,
    categorie_id UUID NOT NULL REFERENCES categories(id),
    nom VARCHAR(255) NOT NULL,
    description TEXT,
    photo_url TEXT,
    prix NUMERIC(10,2) NOT NULL,
    taux_tva NUMERIC(4,2) DEFAULT 0,
    stock INTEGER DEFAULT 0,
    stock_alerte INTEGER DEFAULT 5,
    permets_commande BOOLEAN DEFAULT TRUE,
    etablissement_id UUID NOT NULL REFERENCES etablissements(id) ON DELETE CASCADE,
    created_by UUID REFERENCES utilisateurs(id),
    updated_by UUID REFERENCES utilisateurs(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);

-- =====================================================================
-- 6. COMMANDES
-- =====================================================================
CREATE TABLE commandes (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES utilisateurs(id),
    staff_id UUID REFERENCES utilisateurs(id),
    etablissement_id UUID NOT NULL REFERENCES etablissements(id) ON DELETE CASCADE,
    reference_client VARCHAR(50),
    statut VARCHAR(50) CHECK(statut IN ('en_attente','en_preparation','pret','livre','annule')) DEFAULT 'en_attente',
    type_service VARCHAR(20) CHECK(type_service IN ('sur_place','emporter','livraison')) DEFAULT 'sur_place',
    total NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    montant_tva NUMERIC(10,2) DEFAULT 0.00,
    moyen_paiement VARCHAR(50) CHECK(moyen_paiement IN ('cash','tmoney','flooz','mixte')),
    statut_paiement VARCHAR(50) CHECK(statut_paiement IN ('en_attente','paye','echoue','rembourse')) DEFAULT 'en_attente',
    transaction_id VARCHAR(100),
    created_by UUID REFERENCES utilisateurs(id),
    updated_by UUID REFERENCES utilisateurs(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);

-- =====================================================================
-- 7. LIGNES DE COMMANDE
-- =====================================================================
CREATE TABLE lignes_commande (
    id UUID PRIMARY KEY,
    commande_id UUID NOT NULL REFERENCES commandes(id) ON DELETE CASCADE,
    produit_id UUID NOT NULL REFERENCES produits(id),
    quantite INTEGER NOT NULL CHECK(quantite > 0),
    prix_unitaire NUMERIC(10,2) NOT NULL,
    taux_tva_applique NUMERIC(4,2) DEFAULT 0,
    commentaire TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);

-- =====================================================================
-- 8. MOUVEMENTS DE STOCK
-- =====================================================================
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

-- =====================================================================
-- 9. FACTURES
-- =====================================================================
CREATE TABLE factures (
    id UUID PRIMARY KEY,
    commande_id UUID UNIQUE NOT NULL REFERENCES commandes(id) ON DELETE CASCADE,
    type_facture VARCHAR(20) CHECK(type_facture IN ('facture','avoir')) DEFAULT 'facture',
    facture_parent_id UUID REFERENCES factures(id),
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

-- =====================================================================
-- 10. ÉVALUATIONS
-- =====================================================================
CREATE TABLE evaluations (
    id UUID PRIMARY KEY,
    produit_id UUID NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
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

-- =====================================================================
-- 11. FAQ
-- =====================================================================
CREATE TABLE faqs (
    id UUID PRIMARY KEY,
    etablissement_id UUID NOT NULL REFERENCES etablissements(id) ON DELETE CASCADE,
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

-- =====================================================================
-- 12. SCHEMA VERSION
-- =====================================================================
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    checksum VARCHAR(64),
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(100)
);

-- =====================================================================
-- 13. PAGES D'ÉTABLISSEMENT
-- =====================================================================
CREATE TABLE pages_etablissement (
    id UUID PRIMARY KEY,
    etablissement_id UUID NOT NULL REFERENCES etablissements(id) ON DELETE CASCADE,
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
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);

-- =====================================================================
-- 14. CONFIGURATION DU THÈME WORDPRESS
-- =====================================================================
CREATE TABLE theme_config (
    id UUID PRIMARY KEY,
    etablissement_id UUID NOT NULL REFERENCES etablissements(id) ON DELETE CASCADE,
    theme_id VARCHAR(100) DEFAULT 'artizboard',
    theme_name VARCHAR(255) DEFAULT 'ArtizBoard Default',
    primary_color VARCHAR(7) DEFAULT '#1565C0',
    primary_dark VARCHAR(7) DEFAULT '#0D47A1',
    secondary_color VARCHAR(7) DEFAULT '#00897B',
    accent_color VARCHAR(7) DEFAULT '#E65100',
    surface_color VARCHAR(7) DEFAULT '#F5F7FA',
    background_color VARCHAR(7) DEFAULT '#F5F7FA',
    text_color VARCHAR(7) DEFAULT '#1B1B1F',
    text_soft_color VARCHAR(7) DEFAULT '#455A64',
    error_color VARCHAR(7) DEFAULT '#C62828',
    success_color VARCHAR(7) DEFAULT '#2E7D32',
    font_heading VARCHAR(100) DEFAULT 'Inter',
    font_body VARCHAR(100) DEFAULT 'Inter',
    hero_title VARCHAR(255),
    hero_subtitle TEXT,
    hero_show_button BOOLEAN DEFAULT TRUE,
    hero_button_text VARCHAR(100) DEFAULT 'Voir la carte',
    hero_image_url TEXT,
    nav_show_logo BOOLEAN DEFAULT TRUE,
    nav_show_cart BOOLEAN DEFAULT TRUE,
    nav_sticky BOOLEAN DEFAULT TRUE,
    nav_menu_items JSONB,
    footer_text TEXT DEFAULT '',
    footer_show_social BOOLEAN DEFAULT TRUE,
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
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);

INSERT INTO schema_version (version, filename) VALUES (1, '001_init_supabase.sql');
INSERT INTO schema_version (version, filename) VALUES (2, '002_pages_etablissement.sql');
INSERT INTO schema_version (version, filename) VALUES (3, '003_theme_config.sql');

-- =====================================================================
-- Row Level Security (RLS) — Supabase
-- =====================================================================
ALTER TABLE etablissements ENABLE ROW LEVEL SECURITY;
ALTER TABLE utilisateurs ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE produits ENABLE ROW LEVEL SECURITY;
ALTER TABLE commandes ENABLE ROW LEVEL SECURITY;
ALTER TABLE lignes_commande ENABLE ROW LEVEL SECURITY;
ALTER TABLE faqs ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE pages_etablissement ENABLE ROW LEVEL SECURITY;
ALTER TABLE theme_config ENABLE ROW LEVEL SECURITY;

-- Tables publiques : lecture pour tout le monde (anon + authenticated)
-- Le site WordPress utilise la clé anon pour lire ces données
CREATE POLICY "Public select" ON etablissements FOR SELECT USING (true);
CREATE POLICY "Public select" ON categories FOR SELECT USING (true);
CREATE POLICY "Public select" ON produits FOR SELECT USING (true);
CREATE POLICY "Public select" ON faqs FOR SELECT USING (true);
CREATE POLICY "Public select" ON pages_etablissement FOR SELECT USING (true);
CREATE POLICY "Public select" ON theme_config FOR SELECT USING (true);

-- Commandes : insertion anonyme (site WordPress / portail client)
CREATE POLICY "Anon insert orders" ON commandes FOR INSERT WITH CHECK (true);
CREATE POLICY "Anon select orders" ON commandes FOR SELECT USING (true);

-- Lignes de commande : insertion anonyme
CREATE POLICY "Anon insert lines" ON lignes_commande FOR INSERT WITH CHECK (true);
CREATE POLICY "Anon select lines" ON lignes_commande FOR SELECT USING (true);

-- Utilisateurs : lecture pour auth seulement (données sensibles)
CREATE POLICY "Auth select users" ON utilisateurs FOR SELECT USING (auth.role() = 'authenticated');
