---
tags:
  - skill
  - image-canvas
  - contrainte
  - sous-systeme
  - priorite-3
---

# Sous-système D: Upload + URL

- **D1**: L'image est uploadée dans le bucket `images`, dossier `/{type}/`
- **D2**: L'URL publique est construite : `https://{project}.supabase.co/storage/v1/object/public/images/{type}/{nom}`
- **D3**: Si l'upload échoue, une exception `CaptureError` est levée
- **D4**: L'URL est immédiatement exploitable (pas de délai de cache)
