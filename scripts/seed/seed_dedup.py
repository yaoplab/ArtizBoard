"""Check and deduplicate categories."""
import psycopg2,psycopg2.extras
c=psycopg2.connect(host="127.0.0.1",port=5432,dbname="artizboard_local",
                    user="artizboard",password="artizboard_pass",client_encoding="UTF8")
c.autocommit=True
cur=c.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Show current categories
cur.execute("SELECT nom, count(*) as n FROM categories WHERE deleted_at IS NULL GROUP BY nom ORDER BY n DESC")
for r in cur.fetchall():
    print(f"  {r['nom']}: {r['n']} occurrences")

# Keep only one copy of each (the one with products linked)
# Get first ID for each name
cur.execute("SELECT nom, (array_agg(id ORDER BY id))[1] as fid FROM categories WHERE deleted_at IS NULL GROUP BY nom HAVING count(*)>1")
dupes = [dict(r) for r in cur.fetchall()]

deleted = 0
for d in dupes:
    fid = str(d["fid"])
    cur.execute("SELECT id FROM categories WHERE nom=%s AND id::text!=%s AND deleted_at IS NULL", (d["nom"], fid))
    for row in cur.fetchall():
        cur.execute("UPDATE produits SET categorie_id=%s WHERE categorie_id=%s", (fid, row["id"]))
        cur.execute("UPDATE categories SET deleted_at=NOW() WHERE id=%s", (row["id"],))
        deleted += 1

print(f"\nDeduplicated: {deleted} categories supprimees")
cur.execute("SELECT nom FROM categories WHERE deleted_at IS NULL ORDER BY nom")
for r in cur.fetchall(): print(f"  {r['nom']}")
cur.close();c.close()
