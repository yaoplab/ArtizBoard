---
tags:
  - skill
  - auth-locale
  - fonction
  - systeme-ferme
---

# Fonction Principale

Type: **systeme-ferme**

## 1. Fonction Principale



```
ENTRÉE                              →  TRAITEMENT                        →  SORTIE
email/mot de passe (login)             bcrypt verify + JWT sign          ├─ access_token (JWT)
activation token hex (QR)              SHA-256 match + device register   ├─ refresh_token
user_id + role + etablissement_id      create_token()                    └─ user_info dict
```