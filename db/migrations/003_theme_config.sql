-- =====================================================================
-- ArtizBoard — Migration 003 : Configuration du Thème WordPress
-- =====================================================================

CREATE TABLE theme_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    etablissement_id UUID NOT NULL REFERENCES etablissements(id),

    -- Identité WordPress
    theme_id VARCHAR(100) DEFAULT 'artizboard',
    theme_name VARCHAR(255) DEFAULT 'ArtizBoard Default',
    theme_version VARCHAR(20) DEFAULT '1.0',

    -- Couleurs (override le design system si besoin)
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

    -- Typographie
    font_heading VARCHAR(100) DEFAULT 'Inter',
    font_body VARCHAR(100) DEFAULT 'Inter',
    font_size_base INTEGER DEFAULT 16,
    font_scale_ratio NUMERIC(4,3) DEFAULT 1.25,

    -- Hero / Page d'accueil
    hero_title VARCHAR(255),
    hero_subtitle TEXT,
    hero_show_button BOOLEAN DEFAULT TRUE,
    hero_button_text VARCHAR(100) DEFAULT 'Voir la carte',
    hero_image_url TEXT,

    -- Navigation
    nav_show_logo BOOLEAN DEFAULT TRUE,
    nav_show_cart BOOLEAN DEFAULT TRUE,
    nav_sticky BOOLEAN DEFAULT TRUE,
    nav_menu_items JSONB DEFAULT '[
      {"label":"Accueil","icon":"home","slug":"accueil"},
      {"label":"Carte","icon":"restaurant_menu","slug":"carte"},
      {"label":"À Propos","icon":"info","slug":"apropos"},
      {"label":"Contact","icon":"contact_phone","slug":"contact"}
    ]',

    -- Cartes produits
    card_show_image BOOLEAN DEFAULT TRUE,
    card_show_price BOOLEAN DEFAULT TRUE,
    card_show_description BOOLEAN DEFAULT TRUE,
    card_border_radius INTEGER DEFAULT 12,
    card_shadow BOOLEAN DEFAULT TRUE,

    -- Footer
    footer_text TEXT DEFAULT '© {year} {etablissement_nom} — Tous droits réservés.',
    footer_show_social BOOLEAN DEFAULT TRUE,
    footer_show_hours BOOLEAN DEFAULT TRUE,
    footer_columns JSONB DEFAULT '["Adresse","Horaires","Liens rapides"]',

    -- Performance
    enable_lazy_images BOOLEAN DEFAULT TRUE,
    enable_cache BOOLEAN DEFAULT TRUE,
    cache_duration_minutes INTEGER DEFAULT 5,

    -- CSS personnalisé (admin peut injecter du CSS)
    custom_css TEXT DEFAULT '',
    custom_js TEXT DEFAULT '',

    -- Google
    google_analytics_id VARCHAR(50),
    google_maps_api_key VARCHAR(100),

    -- SEO
    seo_title_template VARCHAR(255) DEFAULT '{page_title} — {etablissement_nom}',
    seo_description TEXT,
    seo_keywords TEXT,

    -- Réseaux sociaux (override etablissements.reseaux_sociaux si besoin)
    facebook_url VARCHAR(255),
    instagram_url VARCHAR(255),
    twitter_url VARCHAR(255),
    tiktok_url VARCHAR(255),
    whatsapp_number VARCHAR(50),

    -- Status
    est_actif BOOLEAN DEFAULT TRUE,

    -- Audit
    created_by UUID REFERENCES utilisateurs(id),
    updated_by UUID REFERENCES utilisateurs(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    sync_status VARCHAR(20) DEFAULT 'local' CHECK(sync_status IN ('local','pending','synced')),
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_theme_config_etablissement ON theme_config(etablissement_id) WHERE deleted_at IS NULL;

-- Valeurs par défaut pour l'établissement existant
INSERT INTO theme_config (id, etablissement_id, theme_id, hero_title, hero_subtitle, hero_image_url)
SELECT uuid_generate_v4(), id, 'artizboard',
       nom,
       COALESCE(mission, 'Bienvenue sur notre portail. Découvrez notre carte et commandez en ligne.'),
       COALESCE(photo_presentation_url, '')
FROM etablissements
WHERE deleted_at IS NULL
AND id NOT IN (SELECT etablissement_id FROM theme_config WHERE deleted_at IS NULL);

INSERT INTO schema_version (version, filename) VALUES (3, '003_theme_config.sql');
