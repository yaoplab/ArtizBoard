# Skill: KDS Kanban (v2 — 10/10)

## When to apply
- Building Kitchen Display System
- Any kanban/status-column layout
- Real-time order tracking for kitchen

## Structure
```
┌──────────────┬──────────────────┬──────────────┐
│ En attente   │ En preparation   │ Pret         │
│ ds.p.tert.   │ ds.p.primary     │ ds.p.success │
├──────────────┼──────────────────┼──────────────┤
│ #ID time T   │ #ID time T       │ #ID time T   │
│ Items list   │ Items list       │ Items list   │
│ Total [→]    │ Total [→]        │ Total        │
└──────────────┴──────────────────┴──────────────┘
  width=190px    width=190px        width=190px
```

## Query — oldest first
```sql
SELECT * FROM commandes
WHERE statut IN ('en_attente','en_preparation','pret')
AND deleted_at IS NULL AND etablissement_id=%s
ORDER BY created_at ASC LIMIT 30
```

## Card format
```python
ft.Container(
    ft.Column([
        # Row 1: ID + elapsed + table
        ft.Row([
            ft.Text(f"#{c['id'][:4]}", 11, BOLD, ds.p.primary),
            ft.Text(f"{mins}m" if mins else "instant", 9, ds.p.text_disabled),
            ft.Container(expand=True),
            ft.Text(f"Table {c.get('reference_client','-')}", 10, ds.p.text_soft),
        ]),
        spacer(ds.space_xxs),
        # Row 2: Items
        ft.Text("2x Poulet  1x Riz  3x Jus", ds.textstyle("body_small")),
        spacer(ds.space_xxs),
        # Row 3: Total + arrow
        ft.Row([
            ft.Text(f"{float(c['total']):,.0f} F", ds.textstyle("label_small"), ds.p.text_soft),
            ft.Container(expand=True),
            # Arrow ONLY if next status exists
            ft.IconButton(ARROW_FORWARD, icon_size=18, icon_color=colors[ns],
                on_click=lambda e, cid=c["id"], ns=next_status: advance(cid,ns))
            if next_status else None,
        ]),
    ]),
    padding=ds.space_sm, bgcolor=ds.p.surface,
    border_radius=ds.SHAPE_SM.radius.top_left,
    border=ft.Border(left=ft.BorderSide(3, column_color)),
)
```

## Colors
```python
colors = {
    "en_attente": ds.p.tertiary,      # orange
    "en_preparation": ds.p.primary,    # blue
    "pret": ds.p.success,             # green
}
```

## Advance command
```python
def advance(cid, ns):
    conn = psycopg2.connect(...)
    cur = conn.cursor()
    cur.execute("UPDATE commandes SET statut=%s WHERE id=%s", (ns, cid))
    conn.commit()
    conn.close()
    refresh_kds()  # Re-render entire view
```

## Auto-refresh (optional polling)
```python
import threading, time
def poll():
    while running:
        time.sleep(10)
        refresh_kds()
threading.Thread(target=poll, daemon=True).start()
```

## Time elapsed
```python
now = datetime.now(timezone.utc)
ctime = c.get("created_at")
if ctime:
    delta = now - ctime.replace(tzinfo=timezone.utc) if ctime.tzinfo is None else now - ctime
    mins = int(delta.total_seconds() / 60)
    time_str = f"{mins}min"
else:
    time_str = ""
```

## Refresh button
```python
ft.IconButton(icon=ft.Icons.REFRESH, icon_size=18,
              on_click=lambda e: refresh_kds())  # header
```

## Mobile/Tablet orientation
```python
# Use landscape on tablet (each column ~190px, scrollable)
kanban = ft.Row(expand=True, spacing=ds.space_sm, scroll=ft.ScrollMode.AUTO)
# On phone: show single column with swipe to change
```

## Emplacement
`apps/staff/__main__.py` — `_kds_view()`, `_ch_kds()`
