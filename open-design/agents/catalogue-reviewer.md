# Agent: Catalogue Reviewer

## Role
Verify the 3-panel catalogue follows the pattern.

## BLOCK on sight
1. No 3-panel layout → must have Categories(left) + Products(mid) + Detail(right)
2. Product list not filtered by selected category
3. .update() called during construction without try/except RuntimeError
4. Delete using CASCADE → must use soft delete
5. Update without version check → must check optimistic lock

## WARN in review
1. Category list missing "Add" button
2. Product list missing "Add" button  
3. Detail panel missing photo, price, stock, description
4. Edit/Delete buttons missing or not functional
5. Refresh functions called during initial construction (should be inline population)
6. Dialog fields missing: nom, catégorie, prix, TVA, stock, alerte, description, disponible
7. Dialog not using ds.SHAPE_MD for shape
8. Confirmation dialog missing for delete

## Checked structure
```
Left(200px)      |  Middle(expand=1)    |  Right(expand=2)
Categories list   |  Products by cat     |  Product detail
• Selection       |  • Stock badge       |  • Photo (or placeholder)
• Highlight       |  • Name + price      |  • Name, Category
• [+Add] button   |  • Selection         |  • Price, Stock, Alert
                  |  • [+Add] button     |  • TVA, Description
                  |                      |  • Availability
                  |                      |  • [Edit] [Delete]
```

## Dialog patterns verified
```
Add/Edit Product:
  Nom, Catégorie(dropdown), Prix, TVA, Stock, Alerte,
  Description(multiline), Disponible(checkbox), Error text
  Actions: [Annuler] [Enregistrer]

Add Category:
  Nom, Error text
  Actions: [Annuler] [Créer]

Confirm Delete:
  Message: "Supprimer {nom} ?"
  Actions: [Annuler] [Supprimer]
```

## Checklist
- [ ] 3 panels: categories, products, detail
- [ ] Category selection filters products
- [ ] Product selection shows detail
- [ ] Stock badge hidden for restaurant type
- [ ] Dialog: all 8 product fields + error
- [ ] Dialog shape: ds.SHAPE_MD
- [ ] Soft delete on products
- [ ] Optimistic lock on product update
- [ ] Category CRUD (add only for now)
- [ ] Refresh via try/except RuntimeError
