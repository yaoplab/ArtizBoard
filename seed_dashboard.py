"""Seed 200+ commandes sur 30 jours."""
import sys, uuid, random
from pathlib import Path
from datetime import datetime, timedelta, timezone
sys.path.insert(0, str(Path(__file__).parent))
import psycopg2, psycopg2.extras

conn = psycopg2.connect(host="127.0.0.1", port=5432, dbname="artizboard_local",
                        user="artizboard", password="artizboard_pass", client_encoding="UTF8")
conn.autocommit = True
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("SELECT id FROM etablissements LIMIT 1")
EID = dict(cur.fetchone())["id"]
cur.execute("SELECT id FROM utilisateurs WHERE email='admin@larepublique.tg'")
AID = dict(cur.fetchone())["id"]
cur.execute("SELECT id, nom, prix FROM produits WHERE deleted_at IS NULL ORDER BY random()")
products = [dict(r) for r in cur.fetchall()]

now = datetime.now(timezone.utc)

# Generate 5-8 commands per day for 30 days (150-240 total)
total = 0
for day in range(30):
    nb = random.randint(5, 8)
    for _ in range(nb):
        cid = str(uuid.uuid4())
        statut = random.choice(["pret", "livre", "livre"])
        paiement = random.choice(["cash", "tmoney", "flooz", "cash"])
        service = random.choice(["sur_place", "sur_place", "emporter", "livraison"])
        table = random.choice(["T1","T2","T3","T4","T5","T6","Comptoir",None])

        n_items = random.randint(1, 4)
        items = random.sample(products, min(n_items, len(products)))
        total_cmd = 0
        for p in items:
            total_cmd += random.randint(1, 4) * float(p["prix"])

        date_cmd = now - timedelta(days=day, hours=random.randint(0, 12))
        cur.execute("""INSERT INTO commandes (id, staff_id, etablissement_id, reference_client,
            statut, type_service, total, moyen_paiement, statut_paiement, created_by, created_at, updated_at)
            VALUES (%s,%s,%s,%s, %s,%s,%s, %s,%s, %s,%s,%s)""",
            (cid, AID, EID, table, statut, service, total_cmd,
             paiement, "paye", AID, date_cmd, date_cmd))
        # Then lignes (FK child)
        for p in items:
            qte = random.randint(1, 4)
            pu = float(p["prix"])
            cur.execute("INSERT INTO lignes_commande (id, commande_id, produit_id, quantite, prix_unitaire) VALUES (%s,%s,%s,%s,%s)",
                       (str(uuid.uuid4()), cid, p["id"], qte, pu))
        total += 1

cur.close()
conn.close()
print(f"OK: {total} commandes inserees (5-8/jour x 30 jours)")
