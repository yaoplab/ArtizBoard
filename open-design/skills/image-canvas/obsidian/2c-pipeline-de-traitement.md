---
tags:
  - skill
  - image-canvas
  - contrainte
  - sous-systeme
  - priorite-2
---

# Sous-système C: Pipeline de traitement

- **C1**: Redimensionner l'image pour que le **plus petit côté** atteigne la dimension cible
- **C2**: Recadrer au centre pour respecter le ratio exact du format
- **C3**: Convertir en **RGB** si nécessaire (supporte PNG, JPEG, BMP, TIFF)
- **C4**: Sauvegarder en **WebP** avec `quality=QUALITY`
- **C5**: Les métadonnées EXIF sont **conservées** (date, orientation)
- **C6**: L'orientation EXIF est appliquée avant redimensionnement
