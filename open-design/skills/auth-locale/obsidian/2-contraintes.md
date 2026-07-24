---
tags:
  - skill
  - auth-locale
  - contrainte
---

# Contraintes Fonctionnelles

## Tableau global

- **C1**: Les mots de passe sont hashés avec **bcrypt** (jamais en clair, jamais SHA/MD5)
- **C2**: Les JWT sont signés avec `SECRET_KEY` lue dans `config.ini`, algorithme HS256
- **C3**: Le JWT expire après `JWT_EXPIRY_MINUTES` (défaut 60 min), contenu : sub, email, role, etablissement_id
- **C4**: Le refresh token est une chaîne hex 32 octets stockée en base avec date d'expiration
- **C5**: En cas d'échec de connexion (3 tentatives), un délai progressif est appliqué (5s, 15s, 60s)
- **C6**: La vérification de token retourne `None` pour token expiré ou invalide (pas d'exception)
- **C7**: Le mode offline fonctionne sans Supabase : l'auth locale est la seule autorité

## [[2a-login-email-mot-de-passe|Sous-système A: Login email/mot de passe]]

## [[2b-activation-qr-code|Sous-système B: Activation QR code]]

## [[2c-gestion-des-devices|Sous-système C: Gestion des devices]]

