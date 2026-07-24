---
tags:
  - skill
  - image-canvas
  - fonction
  - systeme-ferme
---

# Fonction Principale

Type: **systeme-ferme**

## 1. Fonction Principale



```
ENTRÉE                               →  TRAITEMENT                              →  SORTIE
Source (caméra, fichier, scan)         Redimensionner au format cible           ├─ Image traitée (bytes)
Format cible (carte, bannière...)      Rogner si ratio différent                ├─ URL Supabase Storage
Type d'objet (produit, logo, qr)       Compression optimisée (WebP)             ├─ Nom unique (UUID)
                                       Naming rule (uuid_xxx_400x300.webp)      └─ Métadonnées (dimensions, taille)
```

- **Entrée** : Une photo brute depuis caméra ou fichier
- **Sortie** : Une URL publique prête à être stockée en base
- **Traitement** : Redimensionnement → recadrage → compression → upload → URL