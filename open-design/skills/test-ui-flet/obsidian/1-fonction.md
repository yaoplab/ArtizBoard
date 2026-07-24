---
tags:
  - skill
  - test-ui-flet
  - fonction
  - systeme-ouvert
---

# Fonction Principale

Type: **systeme-ouvert**

## 1. Fonction Principale



```
ENTRÉE                              →  TRAITEMENT                           →  SORTIE
App Flet (Admin/Staff/Client)          Lancer app → attendre rendu           ├─ Tests verts/rouges
                                       Simuler clics via page controls       ├─ Capture d'écran (debug)
                                       Vérifier état (dialog ouvert, etc.)  └─ Rapport UI
```

- **Au début** : Une app Flet compilée sans erreur
- **À la fin** : Confirmation que les dialogues, boutons, et navigations fonctionnent
- **Entre les deux** : Automatisation des clics + assertions sur l'état UI