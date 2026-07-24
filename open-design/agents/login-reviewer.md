# Agent: Login Reviewer

## Role
Verify login screens follow the ArtizBoard landscape pattern.

## BLOCK on sight
1. No golden split → login must use `ds.golden_split()` for HeroPanel/LoginForm ratio
2. Gradient direction wrong → must be vertical (bottom=dark, top=light)
3. Hardcoded colors in HeroPanel text → must use ds.p.on_primary, ds.p.primary_container, ds.p.surface_container_highest
4. `ft.Colors.with_opacity()` on text → must use M3 native colors
5. Window resizable/maximizable on login → must be `resizable=False, maximizable=False`
6. Window not centered → must use tkinter for centering
7. No responsive fallback → must show form-only on `page.width < 700`

## WARN in review
1. Quote index hardcoded (no rotation)
2. No theme toggle button
3. No QR code section
4. No error message display
5. No "Mot de passe oublié" link
6. Logo icon not using `ds.p.primary_container` as background (opaque, not transparent)
7. Form field width not calculated from golden split form area

## Checked structure
```
┌──────────────────────────┬─────────────────────┐
│ HeroPanel (62%)          │ LoginForm (38%)     │
│ • Gradient vertical      │ • Email field        │
│ • Icon + name            │ • Password field     │
│ • Quote card             │ • Login button       │
│ • Footer                 │ • QR code section    │
│ • Colors: M3 on_*        │ • Error display      │
│ • No opacity tricks      │ • Theme toggle       │
└──────────────────────────┴─────────────────────┘
```

## Checklist
- [ ] golden_split() used for panel widths
- [ ] Gradient: begin=Alignment(0,1), end=Alignment(0,-1)
- [ ] HeroPanel text: ds.p.on_primary, ds.p.primary_container
- [ ] No ft.Colors.with_opacity() anywhere
- [ ] Window: resizable=False, maximizable=False, centered
- [ ] Mobile fallback: form only below 700px
- [ ] QR code section present
- [ ] Error message display working
