---
tags:
  - skill
  - auth-locale
  - contrainte
  - sous-systeme
  - priorite-1
---

# Sous-système B: Activation QR code

- **B1**: `generate_activation(created_by, user_id)` retourne `(plain_code, qr_url)`
- **B2**: Le code est `secrets.token_hex(4)` = 8 caractères hex = 64 bits d'entropie
- **B3**: Le code est hashé SHA-256 avant stockage (irréversible)
- **B4**: Durée de validité : `ACTIVATION_EXPIRE_MINUTES` (défaut 30 min)
- **B5**: Maximum 3 tentatives (`max_tentatives`), compte incrémenté à chaque échec
- **B6**: L'URL du QR utilise `get_server_config()` pour construire `http://{host}:{port}/activate?token={code}`
