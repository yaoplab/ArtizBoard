-- =====================================================================
-- ArtizBoard — Migration 002 : Pages d'Établissement
-- =====================================================================

CREATE TABLE pages_etablissement (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_pages_etablissement ON pages_etablissement(etablissement_id) WHERE deleted_at IS NULL;

INSERT INTO schema_version (version, filename) VALUES (2, '002_pages_etablissement.sql');
