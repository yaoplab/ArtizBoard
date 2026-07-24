# ArtizBoard — Design System (Open Design compatible)

## CSS Variables (for visual preview)
```css
:root {
  --primary: #1565C0;
  --on-primary: #FFFFFF;
  --primary-container: #BBDEFB;
  --secondary: #00897B;
  --tertiary: #E65100;
  --error: #C62828;
  --success: #2E7D32;
  --surface: #F5F7FA;
  --surface-variant: #E8EAF6;
  --background: #F5F7FA;
  --outline: #546E7A;
  --text-strong: #1B1B1F;
  --text-soft: #455A64;
  --text-disabled: #90A4AE;

  --space-xxs: 4px;
  --space-xs: 8px;
  --space-sm: 12px;
  --space-md: 20px;
  --space-lg: 32px;
  --space-xl: 52px;

  --shape-xs: 4px;
  --shape-sm: 8px;
  --shape-md: 12px;
  --shape-lg: 16px;
  --shape-full: 9999px;

  --font-headline: 700 28px 'Roboto';
  --font-title: 500 16px 'Roboto';
  --font-body: 400 14px 'Roboto';
  --font-label: 500 11px 'Roboto';
}
```

## Brand Identity

ArtizBoard is a commercial management ecosystem (Boutique & Restaurant) for West Africa.
The visual identity conveys trust, professionalism, and modern African commerce.

- **Product**: ArtizBoard
- **Tone**: Professional, modern, warm, accessible
- **Industry**: Commerce, Restaurant, POS
- **Target**: Small business owners, restaurant staff, customers

---

## Color Palette (Material Design v3)

### Core Theme (Blue — default)

| Token | Value | Usage |
|---|---|---|
| `primary` | #1565C0 | Buttons, active states, headers |
| `on_primary` | #FFFFFF | Text on primary background |
| `primary_container` | #BBDEFB | Cards, chips, selected items |
| `on_primary_container` | #001D36 | Text on container |
| `secondary` | #00897B | Accents, success indicators |
| `secondary_container` | #B2DFDB | Secondary surfaces |
| `tertiary` | #E65100 | Warnings, highlights |
| `tertiary_container` | #FFCC80 | Warning surfaces |
| `error` | #C62828 | Errors, destructive actions |
| `error_container` | #FFCDD2 | Error surfaces |
| `success` | #2E7D32 | Positive indicators |
| `surface` | #F5F7FA | Cards, dialogs, panels |
| `surface_variant` | #E8EAF6 | Alternate surfaces, rows |
| `background` | #F5F7FA | Page background |
| `outline` | #546E7A | Borders, dividers |
| `outline_variant` | #B0BEC5 | Light borders |
| `text_strong` | #1B1B1F | Primary text |
| `text_soft` | #455A64 | Secondary text |
| `text_disabled` | #90A4AE | Disabled text |

### Theme Variants

| Theme | Seed | Dark | Character |
|---|---|---|---|
| `blue` | #1565C0 | No | Default — professional, trustworthy |
| `dark` | #212121 | Yes | Night mode, high contrast |
| `sobre` | #37474F | No | Minimalist, elegant |
| `contrast` | #0033A0 | No | High contrast, accessible |

---

## Typography (Material Design v3 Type Scale)

| Style | Size | Weight | Line Height | Usage |
|---|---|---|---|---|
| `display_large` | 57px | Regular | 1.12 | Hero titles |
| `display_medium` | 45px | Regular | 1.15 | Page titles |
| `display_small` | 36px | Regular | 1.22 | Section headers |
| `headline_large` | 32px | Bold | 1.25 | App bar titles |
| `headline_medium` | 28px | Bold | 1.28 | Card titles |
| `headline_small` | 24px | Bold | 1.33 | List headers |
| `title_large` | 22px | Bold | 1.27 | Dialog titles |
| `title_medium` | 16px | Medium | 1.50 | Panel headers |
| `title_small` | 14px | Medium | 1.43 | Subtitles |
| `body_large` | 16px | Regular | 1.50 | Long text |
| `body_medium` | 14px | Regular | 1.43 | Default body |
| `body_small` | 12px | Regular | 1.33 | Captions |
| `label_large` | 14px | Medium | 1.43 | Button text |
| `label_medium` | 12px | Medium | 1.33 | Chip text |
| `label_small` | 11px | Medium | 1.45 | Badges, overlines |

**Font family**: Roboto (primary), Segoe UI (Windows fallback)

---

## Spacing System (Fibonacci × 4px)

All spacing follows the Fibonacci sequence multiplied by a 4px base unit.

| Token | Fibonacci | Pixels | Usage |
|---|---|---|---|
| `space_xxs` | 1 | 4px | Inline gaps, icon-text spacing |
| `space_xs` | 2 | 8px | Tight grouping, chip gaps |
| `space_sm` | 3 | 12px | Standard internal spacing |
| `space_md` | 5 | 20px | Card padding, section gaps |
| `space_lg` | 8 | 32px | Section spacing, dialog padding |
| `space_xl` | 13 | 52px | Large section spacing |
| `space_xxl` | 21 | 84px | Hero spacing, major sections |

**Rule**: NEVER use arbitrary spacing values. Always pick the closest Fibonacci token.
If a gap feels too large or small, go down or up one step (4 → 8 → 12 → 20 → 32 → 52 → 84).

---

## Golden Ratio (φ ≈ 1.618)

Used for macro proportions: panel splits, window dimensions, image aspect ratios.

- **Panel split**: `golden_split(total)` → (large ≈ 62%, small ≈ 38%)
- **Ideal rectangle**: width × height where width/height = φ
- **Window default**: 1100 × 680px (ratio φ)

---

## Shapes & Border Radius

| Token | Radius | Usage |
|---|---|---|
| `SHAPE_NONE` | 0px | Tables, full-width elements |
| `SHAPE_XS` | 4px | Input fields, small cards |
| `SHAPE_SM` | 8px | Buttons, chips, list items |
| `SHAPE_MD` | 12px | Cards, dialogs, panels |
| `SHAPE_LG` | 16px | Large cards, modals |
| `SHAPE_XL` | 28px | Hero containers |
| `SHAPE_FULL` | 9999px | Pills, badges, avatars |

---

## Elevation (Shadows)

| Level | Usage |
|---|---|
| 0 | Flat — text, icons |
| 1 | Cards (resting), list items |
| 2 | Elevated buttons, FAB |
| 3 | Dialogs, dropdowns |
| 4 | Side sheets, nav drawers |
| 5 | Modal overlays |

---

## Component Patterns

### Buttons
- Height: 48px (touch target)
- Radius: SM (8px)
- Variants: Filled, Tonal, Outlined, Text, Elevated
- Padding: h=20px, v=8px

### Cards
- Radius: MD (12px)
- Padding: 20px
- Variants: Elevated, Filled, Outlined
- Min width: 280px

### Input Fields
- Height: 32px
- Radius: XS (4px)
- Border: 1px outline
- Content padding: h=12px, v=8px

### Data Tables
- Header row: surface_variant background
- Row min height: 42px
- Alternating rows: transparent / surface_variant
- Row hover: primary_container

### KPI Cards
- Height: 84px (space_xxl)
- Background: primary_container
- Value text: headline_small
- Label text: label_small

---

## Layout Rules

1. **ZERO hardcoding** — all colors, spacing, typography come from this design system
2. **Fibonacci first** — when in doubt, pick the nearest Fibonacci spacing
3. **Golden ratio for splits** — any two-column layout uses φ
4. **Mobile responsive** — stack vertically below 700px
5. **Login window** — fixed size 1100×680px, centered, non-resizable
6. **Dashboard window** — maximized, resizable

---

## UI States

Every interactive element must handle:
- Default (resting)
- Hover (surface_variant background, cursor pointer)
- Focus (2px primary border, visible focus ring)
- Active/Pressed (darker shade)
- Disabled (reduced opacity, text_disabled color)
- Loading (skeleton shimmer animation)
- Empty (icon + descriptive text)
- Error (error color, clear message)
- Success (success color, confirmation)

---

## Code Conventions

### Flet Implementation (Python)
```python
from ArtizBoardCommon import ds

# Colors — ALWAYS via ds
ds.p.primary          # Primary color
ds.p.surface          # Surface color
ds.p.text_strong      # Text color

# Spacing — ALWAYS via ds
ds.space_md           # 20px
ds.space_lg           # 32px

# Typography — ALWAYS via ds
ds.textstyle("headline_medium")
ds.textstyle("body_medium")

# Shapes
ds.SHAPE_MD.radius.top_left  # 12px

# Proportions
large, small = ds.golden_split(total_width)
```

### Web Implementation (HTML/CSS)
Use CSS custom properties matching the design tokens:
```css
:root {
  --md-sys-color-primary: #1565C0;
  --md-sys-color-surface: #F5F7FA;
  --space-md: 20px;
  --space-lg: 32px;
  --shape-md: 12px;
}
```
