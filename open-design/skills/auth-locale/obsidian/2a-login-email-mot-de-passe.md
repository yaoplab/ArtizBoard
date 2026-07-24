---
tags:
  - skill
  - auth-locale
  - contrainte
  - sous-systeme
  - priorite-3
---

# Sous-système A: Login email/mot de passe

- **A1**: `login(email, password)` retourne `(access_token, refresh_token, user_info)`
- **A2**: En cas d'échec, lève `AuthError` avec message en français
- **A3**: Le mot de passe est vérifié via `bcrypt.checkpw()`
- **A4**: La requête SQL joint `roles` pour obtenir le nom du rôle
