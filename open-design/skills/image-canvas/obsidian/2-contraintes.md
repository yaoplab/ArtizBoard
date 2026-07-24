---
tags:
  - skill
  - image-canvas
  - contrainte
---

# Contraintes Fonctionnelles

## Tableau global

- **C1**: Toute image capturée est redimensionnée à un **format cible** prédéfini
- **C2**: Le ratio est **préservé** — l'image est recadrée (centrée) si nécessaire
- **C3**: Le nom du fichier suit une règle fixe : `{type}_{uuid8}_{largeur}x{hauteur}.webp`
- **C4**: Le format de sortie est **WebP** (compression optimale pour le web)
- **C5**: La compression est configurable : `QUALITY` (défaut 85%)
- **C6**: L'upload se fait vers Supabase Storage dans le dossier `/images/{type}/`
- **C7**: L'URL publique est retournée pour stockage immédiat en base

## [[2a-formats-standards|Sous-système A: Formats standards]]

## [[2b-règles-de-nommage|Sous-système B: Règles de nommage]]

## [[2c-pipeline-de-traitement|Sous-système C: Pipeline de traitement]]

## [[2d-upload-+-url|Sous-système D: Upload + URL]]

