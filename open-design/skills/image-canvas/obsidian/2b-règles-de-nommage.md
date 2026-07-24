---
tags:
  - skill
  - image-canvas
  - contrainte
  - sous-systeme
  - priorite-1
---

# Sous-système B: Règles de nommage

- **B1**: Format : `{type}_{uuid8}_{w}x{h}.webp`
- **B2**: `type` = le format cible (`produit`, `logo`, `banniere`, etc.)
- **B3**: `uuid8` = 8 premiers caractères de `uuid.uuid4().hex`
- **B4**: `{w}x{h}` = dimensions finales de l'image
- **B5**: Exemple : `produit_a1b2c3d4_400x300.webp`
- **B6**: Le nom est garanti **unique** par UUID, évite les collisions
