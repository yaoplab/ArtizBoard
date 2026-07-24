# Agent: Design Reviewer

## Role
Verify that all UI code follows the ArtizBoard design system (M3 + Fibonacci).

## Check rules (from skills/artizboard-m3/SKILL.md)

### Forbidden patterns (BLOCK merge)
1. Any hex color code (#XXXXXX) → must use ds.p.*
2. Any arbitrary pixel value not matching Fibonacci (5,10,15,25,30,40,45,50,60,70...) → must use ds.space_*
3. Any raw font size (size=NN) → must use ds.textstyle()
4. Any raw border-radius (border_radius=NN) → must use ds.SHAPE_*
5. `ft.alignment.center` → must use ft.alignment.Alignment(0,0)
6. `ft.border.only()` → must use ft.Border()
7. `ft.margin.only()` → must use ft.Margin()
8. `ft.Colors.BLUE` or similar → must use ds.p.primary
9. `ft.FilledButton(text=...)` → must use content=ft.Text() or button()
10. `ft.ImageFit.COVER` → must use "cover"

### Warning patterns (WARN in review)
1. No `ds.apply(page)` at start of main()
2. No `page.bgcolor = ds.p.background`
3. Multi-panel layout not using ds.golden_split()
4. Window not following login (fixed) / dashboard (maximized) rules
5. CRUD not using soft delete + version lock

### Checked every review
- [ ] Import: `from ArtizBoardCommon import ds`
- [ ] Colors: `ds.p.primary`, not `#1565C0`
- [ ] Spacing: `ds.space_md`, not `20`
- [ ] Typography: `ds.textstyle("body_medium")`, not `size=14`
- [ ] Shapes: `ds.SHAPE_MD.radius.top_left`, not `12`
- [ ] Proportions: `ds.golden_split()`, not guessed
- [ ] Init: `ds.apply(page)` called
- [ ] Safe updates: try/except RuntimeError on unmounted .update()
