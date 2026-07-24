# Skill: Flet 0.86 Wrapper

## 0. Contexte

**Projet** : ArtizBoard
**Module** : `ArtizBoardCommon/ftw.py` — compatibilité Flet 0.86
**Utilisateurs** : Tous les développeurs
**Dépendances** : [[design-system]]
**Prérequis** : Flet 0.86.x installé

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

### 2. Buttons
```python
❌ ft.FilledButton(text="Click")
✅ ft.FilledButton(content=ft.Text("Click"))

❌ ft.ElevatedButton(text="...")
✅ ft.ElevatedButton(content=ft.Text("..."))

# Tous concernés: Filled, Outlined, Text, Elevated, FilledTonal, IconButton
```

### 3. Cards
```python
❌ ft.Card(surface_tint_color=...)
❌ ft.Card(color=...)
✅ ft.Card(bgcolor=...)
```

### 4. Borders
```python
❌ ft.border.only(right=ft.BorderSide(1, color))
✅ ft.Border(right=ft.BorderSide(1, color))

❌ ft.border.all(1, color)
✅ ft.Border(top=Side(1,c), bottom=Side(1,c), left=Side(1,c), right=Side(1,c))
```

### 5. Margins
```python
❌ ft.margin.only(bottom=20)
✅ ft.Margin(0, 0, 0, 20)  # left, top, right, bottom
```

### 6. Icons
```python
✅ ft.IconButton(icon=ft.Icons.NAME)  # enum, not string
✅ ft.Icon(ft.Icons.NAME)
✅ ft.TextField(prefix_icon="email")  # string OK for fields
```

### 7. Images
```python
❌ ft.Image(fit=ft.ImageFit.COVER)
✅ ft.Image(fit="cover")
```

### 8. Safe update
```python
# List during construction (not mounted)
try: control.update()
except RuntimeError: pass

# Event handler (mounted)
control.update()  # safe
page.update()     # safe
```

### 9. Dialogs (Flet 0.86.1)
```python
# OUVRIR un dialog:
❌ page.dialog = dlg; dlg.open = True; page.update()  # < 0.86.1
✅ page.show_dialog(dlg)  # 0.86.1+

# FERMER un dialog:
❌ page.close_dialog()      # n'existe pas
❌ page.dialog = None        # n'existe plus (lecture)
✅ dlg.open = False; page.update()  # fonctionne partout
```

### 10. FilePicker — NON DISPONIBLE en flet-desktop standard
```python
# FilePicker existe dans l'API Python mais nécessite une compilation Flutter spéciale.
# En l'absence du binaire flet-desktop compilé avec file_picker, l'erreur est:
# "Unknown control: FilePicker"

# SOLUTION: utiliser un champ texte pour les fichiers (chemins locaux)
file_field = ft.TextField(label="Chemin du fichier", hint_text="nom_du_fichier.jpg")
```

### 11. page.snack_bar → Barre d'action
```python
# Depuis 0.86.1 :
❌ page.snack_bar = ft.SnackBar(...); page.snack_bar.open = True
✅ page.snack_bar = ft.SnackBar(content=ft.Text("Message"), open=True)
✅ page.update()
```
```python
❌ page.window.center()  # async, can't await in sync main()
✅ Use tkinter:
import tkinter as tk
root = tk.Tk()
sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
root.destroy()
page.window.left = (sw - w) // 2
page.window.top = (sh - h) // 2
```

### 10. SnackBar
```python
❌ page.snack_bar = ft.SnackBar(...)
✅ page.snack_bar = ft.SnackBar(content=ft.Text("Message"), bgcolor=..., duration=3000)
   page.snack_bar.open = True
   page.update()
```

### 11. DataTable
```python
# border: only bottom supported
ft.DataTable(
    border=ft.Border(bottom=ft.BorderSide(1, color)),
    heading_row_color=surface_variant,
    data_row_min_height=42,
    column_spacing=ds.space_md,
)
```

### 12. Dropdown
```python
options=[ft.dropdown.Option(value, label)]  # lowercase 'dropdown'
value=str(uuid)  # always string
```

### 13. ft.app() launch
```python
# Desktop
if __name__ == "__main__":
    ft.app(target=main)

# Mobile (APK)
# flet build apk run_staff.py --name "ArtizBoard Staff"
```

### 14. Debug & Crash Protection — OBLIGATOIRE sur tous les handlers

```python
from ArtizBoardCommon.debug import safe_handler, set_debug

# Avant les tests : activer le debug
set_debug(True)

# Tout handler de bouton/event DOIT etre wrappe :
btn = ft.FilledButton("OK", on_click=safe_handler(mon_handler, "Admin.btn_ok"))

# Une fois les tests passes : desactiver
set_debug(False)
```

| # | Contrainte |
|---|---|
| 14.1 | Tout `on_click=` d'un `ft.Button`/`ft.IconButton` est wrappe avec `safe_handler()` |
| 14.2 | Tout `on_change=` d'un `ft.Dropdown`/`ft.TextField` est wrappe avec `safe_handler()` |
| 14.3 | Chaque handler a un label unique : `"App.Section.action"` (ex: `"Admin.catalogue.save_produit"`) |
| 14.4 | En debug : log START/OK/ERROR avec temps d'execution |
| 14.5 | En erreur : affiche une snackbar rouge avec le message, jamais de crash silencieux |
| 14.6 | `set_debug(False)` avant la livraison ou apres les tests |
| 14.7 | Les tests verifient que `safe_handler` ne leve pas d'exception sur erreur |

## Quick debug checklist
Quand Flet crash avec "unexpected keyword argument":
1. Button → `text=` → `content=ft.Text()`
2. Card → `color=`, `surface_tint_color=` → `bgcolor=`
3. Border → `ft.border.only()` → `ft.Border(right=...)`
4. Margin → `ft.margin.only()` → `ft.Margin(l,t,r,b)`
5. Alignment → `ft.alignment.center` → `ft.alignment.Alignment(0,0)`
6. Image → `ft.ImageFit.COVER` → `"cover"`
7. Icon → lowercase string → `ft.Icons.NAME`

## Emplacement
`ArtizBoardCommon/ftw.py` — wrapper complet
`ArtizBoardCommon/components.py` — composants sécurisés
