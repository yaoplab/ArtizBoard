---
tags:
  - skill
  - login-paysage
  - contrainte
  - sous-systeme
  - priorite-1
---

# Sous-système B: LoginForm

- **B1**: Bouton "Mot de passe oublié" redirige (placeholder)
- **B2**: La section QR code est toujours visible sous le formulaire
- **B3**: Le champ mot de passe peut révéler le texte (`can_reveal_password`)
- **B4**: La validation est déclenchée par le bouton OU la touche Entrée (`on_submit`)
- **B5**: Les champs utilisent `textfield()` de ArtizBoardCommon, pas `ft.TextField` brut
