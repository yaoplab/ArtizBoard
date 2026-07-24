---
tags:
  - skill
  - login-paysage
  - contrainte
---

# Contraintes Fonctionnelles

## Tableau global

- **C1**: La fenêtre login est **fixe** : `resizable=False`, `maximizable=False`
- **C2**: Les dimensions suivent le **golden ratio** : `ds.golden_width(680)` = ~1100 × 680 px
- **C3**: La fenêtre est **centrée** sur l'écran via tkinter
- **C4**: Le layout est un split **62%/38%** : HeroPanel à gauche, LoginForm à droite
- **C5**: Le HeroPanel utilise un gradient vertical primaire → container → background
- **C6**: Le LoginForm supporte l'auth email/mdp ET le QR code d'activation
- **C7**: En **mobile** (<700px), seul le LoginForm est affiché (pas de HeroPanel)

## [[2a-heropanel|Sous-système A: HeroPanel]]

## [[2b-loginform|Sous-système B: LoginForm]]

