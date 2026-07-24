# Agent: KDS Reviewer

## Role
Verify the Kitchen Display System (Kanban) follows the pattern.

## BLOCK on sight
1. Wrong number of columns → must have 3: en_attente, en_preparation, pret
2. Wrong order direction → must be `ORDER BY created_at ASC` (oldest first)
3. Missing status color coding → each column MUST have its M3 color
4. Arrow button on "pret" column → "pret" has no next status

## WARN in review
1. Card missing: command ID (#XXXX), elapsed time, table ref
2. Card missing: items list (qty × name)
3. Card missing: total amount
4. Card missing: arrow button for valid transitions
5. No refresh button
6. No count badge on column headers
7. Left border color not matching column color
8. Column width too narrow (< 180px) or too wide (> 250px)

## Checked structure
```
┌──────────────┬──────────────────┬──────────────┐
│ En attente   │ En préparation   │ Prêt         │
│ [count]      │ [count]          │ [count]       │
├──────────────┼──────────────────┼──────────────┤
│ #a1b2 3m T1  │ #c3d4 12m T3     │ #e5f6 25m T2 │
│ 2x poulet    │ 1x riz gras      │ 1x poisson   │
│ 1x bissap    │ [→]              │ (pas de →)   │
│ 8000F [→]    │ 5000F [→]        │ 8000F        │
└──────────────┴──────────────────┴──────────────┘
```

## Status colors verified
```
en_attente     → ds.p.tertiary    (orange)
en_preparation → ds.p.primary     (blue)
pret           → ds.p.success     (green)
```

## Flow verified
```
en_attente → [→] → en_preparation → [→] → pret
                       advance(cid, ns)    → UPDATE commandes SET statut=ns
                                           → refresh_kds()
```

## Checklist
- [ ] 3 columns: en_attente, en_preparation, pret
- [ ] Colors: tertiary, primary, success
- [ ] Order: ASC (oldest first)
- [ ] Card: #ID + time + table + items + total + arrow
- [ ] Arrow only on en_attente and en_preparation
- [ ] Arrow click → UPDATE statut → refresh
- [ ] Count badge on each column header
- [ ] Refresh button present
- [ ] Column width 190px
- [ ] Left border color matches column
