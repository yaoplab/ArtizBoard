# Guide Administrateur — ArtizBoard

## Premier démarrage
1. Lancer `python -m apps.admin`
2. Créer le compte admin + établissement
3. Se connecter avec email/mot de passe

## Gestion du catalogue
- **Menu Établissement → Pages → Ajouter une page** pour créer du contenu web
- **Menu Établissement → Apparence** pour personnaliser couleurs, hero, SEO
- **Menu Catalogue** → ajouter/modifier/supprimer des produits
- Les modifications sont synchronisées vers le site web via Supabase

## Gestion des utilisateurs
- **Menu Utilisateurs** → créer des comptes staff
- Générer un code QR pour l'activation des appareils
- Révoquer un appareil si nécessaire

## Dashboard & Rapports
- **Menu Dashboard** → KPIs en temps réel
- **Menu Rapports** → exporter CSV ou PDF

## Site Web
- Le site public lit les données depuis Supabase
- Toute modification dans l'Admin est visible sur le site après synchro
- Pour déployer une mise à jour du thème : `python deploy_site.py`