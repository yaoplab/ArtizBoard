"""Test rapide: supprimer une categorie vide."""
import psycopg2, uuid
c = psycopg2.connect(host='127.0.0.1', port=55515, dbname='ArtizBoard', user='postgres', password='postgres')
cur = c.cursor()

# Trouver admin
cur.execute("SELECT id FROM utilisateurs LIMIT 1")
uid = cur.fetchone()[0]

# Trouver etablissement
cur.execute("SELECT id FROM etablissements LIMIT 1")
eid = cur.fetchone()[0]

# Créer catégorie vide test
cid = str(uuid.uuid4())
cur.execute("INSERT INTO categories (id, nom, etablissement_id, created_by, updated_by) VALUES (%s,%s,%s,%s,%s)",
            (cid, "Test Vide", eid, uid, uid))
c.commit()
print(f"Categorie test creee: {cid[:8]}")

# Vérifier qu'elle n'a pas de produits
cur.execute("SELECT COUNT(*) FROM produits WHERE categorie_id=%s AND deleted_at IS NULL", (cid,))
nb = cur.fetchone()[0]
print(f"Produits dans cat: {nb}")

# Supprimer
cur.execute("UPDATE categories SET deleted_at=NOW(), updated_by=%s WHERE id=%s AND deleted_at IS NULL", (uid, cid))
c.commit()
print(f"Rows updated: {cur.rowcount}")

# Vérifier
cur.execute("SELECT id FROM categories WHERE id=%s AND deleted_at IS NULL", (cid,))
print("OK supprimee" if cur.fetchone() is None else "ERREUR: toujours la")

cur.close(); c.close()
