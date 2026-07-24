"""Clean & reseed commands with proper FK constraints."""
import sys, uuid, random
from pathlib import Path
from datetime import datetime, timedelta, timezone
sys.path.insert(0, str(Path(__file__).parent))
import psycopg2, psycopg2.extras

conn = psycopg2.connect(host="127.0.0.1", port=5432, dbname="artizboard_local",
                        user="artizboard", password="artizboard_pass", client_encoding="UTF8")
conn.autocommit = True
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get IDs
cur.execute("SELECT id FROM etablissements LIMIT 1")
EID = str(cur.fetchone()["id"])
cur.execute("SELECT id FROM utilisateurs WHERE email='admin@larepublique.tg'")
AID = str(cur.fetchone()["id"])

# Clean: delete factures first, then lignes, then commandes (FK order)
cur.execute("DELETE FROM factures")
cur.execute("DELETE FROM lignes_commande")
cur.execute("DELETE FROM commandes")
print("Cleaned all commands, lignes, factures.")

# Get products
cur.execute("SELECT id, nom, prix FROM produits WHERE deleted_at IS NULL ORDER BY random()")
products = [dict(r) for r in cur.fetchall()]

# Get staff users
cur.execute("SELECT id FROM utilisateurs WHERE role_id=(SELECT id FROM roles WHERE nom='serveur') LIMIT 1")
staff_row = cur.fetchone()
staff_id = str(staff_row["id"]) if staff_row else AID

# Create staff if not exists
if not staff_row:
    cur.execute("SELECT id FROM roles WHERE nom='serveur'")
    role = cur.fetchone()
    new_staff = str(uuid.uuid4())
    cur.execute("""INSERT INTO utilisateurs (id, etablissement_id, nom, email, role_id, created_by, updated_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (new_staff, EID, "Kofi", "kofi@larepublique.tg", role["id"], AID, AID))
    staff_id = new_staff

now = datetime.now(timezone.utc)
total = 0

for day in range(30):
    nb = random.randint(4, 7)
    for _ in range(nb):
        cid = str(uuid.uuid4())
        statut = random.choice(["pret", "livre", "livre", "pret", "en_preparation"])
        paiement = random.choice(["cash", "tmoney", "flooz", "cash", "cash"])
        service = random.choice(["sur_place", "sur_place", "sur_place", "emporter", "livraison"])
        table = random.choice(["T1","T2","T3","T4","T5","T6","Comptoir",None])

        n_items = random.randint(1, 4)
        items = random.sample(products, min(n_items, len(products)))
        total_cmd = 0
        for p in items:
            qte = random.randint(1, 4)
            pu = float(p["prix"])
            total_cmd += pu * qte

        date_cmd = now - timedelta(days=day, hours=random.randint(0, 12))

        # INSERT commande FIRST (FK parent)
        cur.execute("""INSERT INTO commandes (id, staff_id, etablissement_id, reference_client,
            statut, type_service, total, moyen_paiement, statut_paiement, created_by, created_at, updated_at)
            VALUES (%s,%s,%s,%s, %s,%s,%s, %s,%s, %s,%s,%s)""",
            (cid, staff_id, EID, table, statut, service, total_cmd,
             paiement, "paye", AID, date_cmd, date_cmd))

        # THEN lignes (FK child)
        for p in items:
            qte = random.randint(1, 4)
            pu = float(p["prix"])
            cur.execute("INSERT INTO lignes_commande (id, commande_id, produit_id, quantite, prix_unitaire) VALUES (%s,%s,%s,%s,%s)",
                       (str(uuid.uuid4()), cid, p["id"], qte, pu))
        total += 1

# Verify
cur.execute("SELECT count(*), sum(total) FROM commandes WHERE deleted_at IS NULL")
r = cur.fetchone()
cur.execute("SELECT count(*) FROM lignes_commande")
lc = cur.fetchone()

cur.close(); conn.close()
print(f"OK: {total} commandes, {r[0]} total DB, {lc[0]} lignes, CA={r[1]:,.0f} F")
print("Lance: python -m apps.admin → Dashboard + Commandes")
