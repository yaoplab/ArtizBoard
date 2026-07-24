---
tags:
  - skill
  - flet-wrapper
  - fonction
  - systeme-ferme
---

# Fonction Principale

Type: **systeme-ferme**

## 1. Fonction Principale

### Type : Systeme Ferme

**Entrée** : Composant Flet avec ancienne API (< 0.86)
**Sortie** : Composant compatible Flet 0.86+
**Traitement** : Remplacer API dépréciées (ElevatedButton → Button, tuples → Alignment, etc.)


## When to apply
- Any Flet 0.86 code that touches alignment, buttons, cards, borders, margins, images, icons, or window management
- Debugging Flet API errors ("unexpected keyword argument", "has no attribute")
- Code review of Flet UI code

## 10 règles avec ❌/✅

### 1. Alignment
```python
❌ ft.alignment.center
✅ ft.alignment.Alignment(0, 0)

❌ ft.alignment.top_left
✅ ft.alignment.Alignment(-1, -1)
```

#