-- =====================================================================
-- ArtizBoard — Schéma PostgreSQL Local (v2)
-- Livrable A — init_pg_local.sql
-- =====================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================================
-- 1. ÉTABLISSEMENTS
-- =====================================================================
CREATE TABLE etablissements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nom VARCHAR(50) UNIQUE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Permissions par défaut
INSERT INTO permissions (id, code) VALUES
    (uuid_generate_v4(), 'create_order'),
    (uuid_generate_v4(), 'manage_stock'),
    (uuid_generate_v4(), 'view_dashboard'),
    (uuid_generate_v4(), 'manage_establishment'),
    (uuid_generate_v4(), 'print_invoice'),
    (uuid_generate_v4(), 'manage_users'),
    (uuid_generate_v4(), 'view_reports'),
    (uuid_generate_v4(), 'process_payment'),
    (uuid_generate_v4(), 'manage_faq'),
    (uuid_generate_v4(), 'manage_categories');

-- Rôles par défaut
INSERT INTO roles (id, nom) VALUES
    (uuid_generate_v4(), 'admin'),
    (uuid_generate_v4(), 'gerant'),
    (uuid_generate_v4(), 'caissier'),
    (uuid_generate_v4(), 'serveur'),
    (uuid_generate_v4(), 'cuisinier');

-- Admin a toutes les permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p WHERE r.nom = 'admin';

-- =====================================================================
-- 3. UTILISATEURS
-- =====================================================================
CREATE TABLE utilisateurs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    etablissement_id UUID NOT NULL REFERENCES etablissements(id),
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

-- =====================================================================
-- 5. PRODUITS / PLATS
-- =====================================================================
CREATE TABLE produits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    categorie_id UUID NOT NULL REFERENCES categories(id),
    nom VARCHAR(255) NOT NULL,
    description TEXT,
    photo_url TEXT,
    prix NUMERIC(10,2) NOT NULL,
    taux_tva NUMERIC(4,2) DEFAULT 0,
    stock INTEGER DEFAULT 0,
    stock_alerte INTEGER DEFAULT 5,
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

-- =====================================================================
-- 6. COMMANDES
-- =====================================================================
CREATE TABLE commandes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES utilisateurs(id),
    staff_id UUID REFERENCES utilisateurs(id),
    etablissement_id UUID NOT NULL REFERENCES etablissements(id),
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commande_id UUID NOT NULL REFERENCES commandes(id),
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commande_id UUID UNIQUE NOT NULL REFERENCES commandes(id),
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

-- =====================================================================
-- 11. FAQ
-- =====================================================================
CREATE TABLE faqs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

-- =====================================================================
-- 12. CODES D'ACTIVATION
-- =====================================================================
CREATE TABLE activation_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code_hash TEXT NOT NULL,
    utilisateur_id UUID REFERENCES utilisateurs(id),
    cree_par UUID NOT NULL REFERENCES utilisateurs(id),
    tentative_count INTEGER DEFAULT 0,
    max_tentatives INTEGER DEFAULT 3,
    expire_le TIMESTAMP WITH TIME ZONE NOT NULL,
    utilise_le TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
);

-- =====================================================================
-- 13. DEVICES
-- =====================================================================
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    utilisateur_id UUID NOT NULL REFERENCES utilisateurs(id),
    device_name VARCHAR(100),
    device_ip VARCHAR(45),
    dernier_acces TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    est_revoque BOOLEAN DEFAULT FALSE,
    revoque_par UUID REFERENCES utilisateurs(id),
    revoque_le TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- 14. BACKUPS
-- =====================================================================
CREATE TABLE backups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

-- =====================================================================
-- 15. SCHEMA VERSION (migrations)
-- =====================================================================
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    checksum VARCHAR(64),
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(100) DEFAULT 'init_pg_local.sql'
);

INSERT INTO schema_version (version, filename) VALUES (1, '001_init_pg_local.sql');

-- =====================================================================
-- SÉQUENCE POUR NUMÉROS DE FACTURE
-- =====================================================================
CREATE SEQUENCE IF NOT EXISTS seq_numero_facture START 1;

-- =====================================================================
-- INDEX
-- =====================================================================
CREATE INDEX idx_produits_etablissement ON produits(etablissement_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_produits_categorie ON produits(categorie_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_commandes_etablissement ON commandes(etablissement_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_commandes_statut ON commandes(statut) WHERE deleted_at IS NULL;
CREATE INDEX idx_commandes_client ON commandes(client_id) WHERE deleted_at IS NULL AND client_id IS NOT NULL;
CREATE INDEX idx_lignes_commande_commande ON lignes_commande(commande_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_mouvements_stock_produit ON mouvements_stock(produit_id);
CREATE INDEX idx_mouvements_stock_commande ON mouvements_stock(commande_id) WHERE commande_id IS NOT NULL;
CREATE INDEX idx_factures_commande ON factures(commande_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_evaluations_produit ON evaluations(produit_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_faqs_etablissement ON faqs(etablissement_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_utilisateurs_etablissement ON utilisateurs(etablissement_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_devices_utilisateur ON devices(utilisateur_id) WHERE est_revoque = FALSE;
