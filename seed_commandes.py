"""ArtizBoard — Seed Commandes : 10 commandes de test
Idempotent. Relance sans risque.
Usage: python seed_commandes.py
"""
import sys, uuid, logging, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import psycopg2, psycopg2.extras
from ArtizBoardCommon.config_loader import get_db_config

logging.basicConfig(level=logging.INFO, format="[seed-cmd] %(message)s")
log = logging.getLogger("seed_cmd")

db = get_db_config()
conn = psycopg2.connect(host=db[0], port=db[1], dbname=db[2],
                        user=db[3], password=db[4], client_encoding="UTF8")
conn.autocommit = False

def uid(): return str(uuid.uuid4())

def main():
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT id, nom FROM etablissements WHERE deleted_at IS NULL LIMIT 1")
    etab = cur.fetchone()
    if not etab:
        log.error("Aucun etablissement. Lancez d'abord seed_db.py")
        return
    eid = etab['id']
    log.info(f"Etablissement : {etab['nom']}")

    cur.execute("SELECT id FROM utilisateurs WHERE etablissement_id=%s AND deleted_at IS NULL LIMIT 1", (eid,))
    user_row = cur.fetchone()
    if not user_row:
        log.error("Aucun utilisateur. Lancez d'abord seed_db.py")
        return
    user_id = user_row['id']

    cur.execute("SELECT id, nom, prix, stock FROM produits WHERE etablissement_id=%s AND deleted_at IS NULL ORDER BY RANDOM() LIMIT 30", (eid,))
    prods = [dict(r) for r in cur.fetchall()]
    if not prods:
        log.error("Aucun produit. Lancez d'abord seed_db.py")
        return
    log.info(f"{len(prods)} produits disponibles")

    cur.execute("SELECT MAX(numero_facture) as m FROM factures")
    max_fac = cur.fetchone()
    fac_seq = 0
    if max_fac and max_fac['m']:
        import re
        m = re.search(r'(\d{5})$', max_fac['m'])
        if m:
            fac_seq = int(m.group(1))

    from datetime import datetime, timedelta
    today = datetime.now()
    base = today - timedelta(days=30)

    STATUSES = ['en_attente', 'en_preparation', 'pret', 'livre', 'annule']
    PAYMENT_STATUSES = ['en_attente', 'paye', 'echoue', 'rembourse']
    MOYENS = ['cash', 'tmoney', 'flooz', 'mixte']
    TYPES = ['sur_place', 'emporter', 'livraison']
    TABLES = ['T01', 'T02', 'T03', 'T05', 'T08', 'T12', None]

    cmd_ids = []
    total_lignes = 0
    total_factures = 0
    total_mvt_stock = 0

    log.info("Suppression anciennes commandes de seed...")
    cur.execute("DELETE FROM mouvements_stock WHERE produit_id IN (SELECT id FROM produits WHERE etablissement_id=%s)", (eid,))
    cur.execute("DELETE FROM lignes_commande WHERE commande_id IN (SELECT id FROM commandes WHERE etablissement_id=%s)", (eid,))
    cur.execute("DELETE FROM factures WHERE commande_id IN (SELECT id FROM commandes WHERE etablissement_id=%s)", (eid,))
    cur.execute("DELETE FROM commandes WHERE etablissement_id=%s", (eid,))
    conn.commit()

    log.info("Creation des 10 commandes...")

    for i in range(10):
        cid = uid()
        cmd_ids.append(cid)
        statut = STATUSES[i % len(STATUSES)]
        pstatut = 'paye' if statut in ('pret', 'livre') else random.choice(['en_attente', 'paye'])
        moyen = random.choice(MOYENS) if pstatut == 'paye' else None
        tservice = random.choice(TYPES)
        table_ref = random.choice(TABLES)
        ref = table_ref if table_ref else 'Web'
        created_date = base + timedelta(days=i * 3)

        # Build lines first to compute total
        n_lines = random.randint(1, 5)
        sample_prods = random.sample(prods, min(n_lines, len(prods)))
        lines = []
        total = 0
        for p in sample_prods:
            qty = random.randint(1, 3)
            total += float(p['prix']) * qty
            lines.append((p, qty))

        total = round(total, 2)

        cur.execute("""
            INSERT INTO commandes (id, etablissement_id, reference_client,
                statut, type_service, total, moyen_paiement, statut_paiement,
                created_by, updated_by, created_at, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (cid, eid, ref, statut, tservice, total, moyen, pstatut,
              user_id, user_id, created_date, created_date))

        # Insert lignes_commande
        for p, qty in lines:
            lid = uid()
            cur.execute("""
                INSERT INTO lignes_commande (id, commande_id, produit_id, quantite, prix_unitaire)
                VALUES (%s,%s,%s,%s,%s)
            """, (lid, cid, p['id'], qty, p['prix']))
            total_lignes += 1

            # Mouvement de stock : sortie_vente
            mid = uid()
            cur.execute("""
                INSERT INTO mouvements_stock (id, produit_id, commande_id,
                    ligne_commande_id, type_mouvement, quantite, motif, created_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (mid, p['id'], cid, lid, 'sortie_vente', qty,
                  f"Commande #{cid[:8]}", user_id))
            total_mvt_stock += 1

        # Factures for completed orders (livre)
        if statut == 'livre' and pstatut == 'paye':
            fac_seq += 1
            fid = uid()
            seq_str = f"{fac_seq:05d}"
            annee_mois = created_date.strftime('%Y%m%d')
            num = f"FAC-{annee_mois}-{seq_str}"
            cur.execute("""
                INSERT INTO factures (id, commande_id, type_facture,
                    numero_facture, date_emission, imprimee, created_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (fid, cid, 'facture', num, created_date, True, user_id))
            total_factures += 1

    conn.commit()
    cur.close()

    log.info(f"Termine : {len(cmd_ids)} commandes, {total_lignes} lignes, {total_factures} factures, {total_mvt_stock} mouvements stock")

    stats = {
        'en_attente': 0, 'en_preparation': 0, 'pret': 0, 'livre': 0, 'annule': 0
    }
    for i, s in enumerate(STATUSES):
        if i < len(cmd_ids):
            stats[s] += 1
    print("\n=== Commandes de test creees ===")
    for s, n in stats.items():
        if n > 0:
            print(f"  {s}: {n}")
    print(f"\n{len(cmd_ids)} commandes, {total_lignes} lignes, {total_factures} factures created")

if __name__ == "__main__":
    main()
    conn.close()
