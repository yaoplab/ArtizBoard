-- Correctif : ajout des colonnes d'audit manquantes dans Supabase
-- Exécuter dans SQL Editor Supabase

ALTER TABLE roles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE permissions ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'synced';
ALTER TABLE permissions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
ALTER TABLE role_permissions ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'synced';
ALTER TABLE role_permissions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
ALTER TABLE role_permissions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE mouvements_stock ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

-- Supprimer les FK récursives qui empêchent l'upsert
ALTER TABLE categories DROP CONSTRAINT IF EXISTS categories_created_by_fkey;
ALTER TABLE categories DROP CONSTRAINT IF EXISTS categories_updated_by_fkey;
ALTER TABLE produits DROP CONSTRAINT IF EXISTS produits_created_by_fkey;
ALTER TABLE produits DROP CONSTRAINT IF EXISTS produits_updated_by_fkey;
ALTER TABLE faqs DROP CONSTRAINT IF EXISTS faqs_created_by_fkey;
ALTER TABLE faqs DROP CONSTRAINT IF EXISTS faqs_updated_by_fkey;
ALTER TABLE pages_etablissement DROP CONSTRAINT IF EXISTS pages_etablissement_created_by_fkey;
ALTER TABLE pages_etablissement DROP CONSTRAINT IF EXISTS pages_etablissement_updated_by_fkey;
ALTER TABLE theme_config DROP CONSTRAINT IF EXISTS theme_config_created_by_fkey;
ALTER TABLE theme_config DROP CONSTRAINT IF EXISTS theme_config_updated_by_fkey;
ALTER TABLE commandes DROP CONSTRAINT IF EXISTS commandes_client_id_fkey;
ALTER TABLE commandes DROP CONSTRAINT IF EXISTS commandes_staff_id_fkey;
ALTER TABLE commandes DROP CONSTRAINT IF EXISTS commandes_created_by_fkey;
ALTER TABLE commandes DROP CONSTRAINT IF EXISTS commandes_updated_by_fkey;
ALTER TABLE lignes_commande DROP CONSTRAINT IF EXISTS lignes_commande_produit_id_fkey;
