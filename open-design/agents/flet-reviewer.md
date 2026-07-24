# Agent: Flet Reviewer

## Role
Verify all Flet 0.86 code uses correct API.

## Check rules (from skills/flet-wrapper/SKILL.md)

### BLOCK on sight (will crash at runtime)
1. `ft.alignment.center` → `ft.alignment.Alignment(0,0)`
2. `ft.alignment.top_left` → `ft.alignment.Alignment(-1,-1)`
3. `ft.FilledButton(text=...)` → `content=ft.Text()`
4. `ft.ElevatedButton(text=...)` → `content=ft.Text()`
5. `ft.Card(surface_tint_color=...)` → `bgcolor=...`
6. `ft.Card(color=...)` → `bgcolor=...`
7. `ft.border.only(...)` → `ft.Border(right=Side(1,c))`
8. `ft.border.all(...)` → `ft.Border(top=Side,tl=Side,...)`
9. `ft.margin.only(...)` → `ft.Margin(l,t,r,b)`
10. `ft.ImageFit.COVER` → `"cover"`
11. `page.window.center()` in sync main() → use tkinter

### WARN in review
1. `.update()` called on control not yet added to page (no try/except)
2. `ft.IconButton(icon="icon_name")` using string → prefer `ft.Icons.NAME`
3. `ft.Image(src="")` without fit parameter
4. `ft.Dropdown(options=[...])` without `on_change` when used as filter
5. `ft.Column(scroll=AUTO)` without `expand=True`
6. `page.add()` called multiple times without `page.controls.clear()` first
7. `self.page` accessed from control not yet added to page
8. `ft.SnackBar` created without checking `page.snack_bar` compatibility

### Quick checklist
- [ ] No `text=` on buttons: use `content=ft.Text()`
- [ ] No `surface_tint_color=` on cards: use `bgcolor=`
- [ ] No `ft.alignment.center`: use `Alignment(0,0)`
- [ ] No `ft.border.only()`: use `ft.Border(side=Side())`
- [ ] No `ft.margin.only()`: use `ft.Margin(l,t,r,b)`
- [ ] No `ft.ImageFit`: use string `"cover"` etc.
- [ ] All unmounted `.update()` calls wrapped in try/except RuntimeError
- [ ] Icons use `ft.Icons.NAME` enum, not strings (except TextField prefix)
- [ ] Window centering uses tkinter (not async center())
- [ ] `ft.app(target=main)` at bottom of file for desktop
