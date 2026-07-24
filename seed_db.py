"""ArtizBoard — Seed Database : Restaurant La Republique

Idempotent. Relance sans risque.
Usage: python seed_db.py
"""

import sys, uuid, logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import psycopg2, psycopg2.extras
from ArtizBoardCommon.config_loader import get_db_config

logging.basicConfig(level=logging.INFO, format="[seed] %(message)s")
log = logging.getLogger("seed")

db = get_db_config()
conn = psycopg2.connect(host=db[0], port=db[1], dbname=db[2],
                        user=db[3], password=db[4], client_encoding="UTF8")
conn.autocommit = False

def uid(): return str(uuid.uuid4())

ETAB_ID = uid()
ADMIN_ID = uid()

CATS = [
    ("Entr\u00e9es", "restaurant_menu"),
    ("Plats Principaux", "lunch_dining"),
    ("Grillades & Poisson", "set_meal"),
    ("Accompagnements", "bakery_dining"),
    ("Desserts", "cake"),
    ("Boissons Fraiches", "local_drink"),
    ("Boissons Chaudes", "coffee"),
]

PLATS = [
    ("Entr\u00e9es", "Salade Beninoise", "Salade verte, tomate, oignon, carotte, oeuf dur, thon", 2500),
    ("Entr\u00e9es", "Beignets de Poisson", "Beignets de maquereau epices, sauce tomate", 2000),
    ("Entr\u00e9es", "Samoussas Viande", "6 pieces, farce boeuf hache, oignon, persil, ail", 2000),
    ("Entr\u00e9es", "Brochettes de Poulet", "3 brochettes marinees, sauce arachide", 3000),
    ("Entr\u00e9es", "Garba (Attieke Poisson)", "Attieke, poisson thon grille, oignon, piment", 3500),
    ("Plats Principaux", "Riz au Gras (Thieboudiene)", "Riz parfume, poisson frais, legumes varies, sauce tomate", 5000),
    ("Plats Principaux", "Sauce d'Arachide", "Sauce arachide onctueuse, poulet, riz blanc", 4500),
    ("Plats Principaux", "Sauce Graine (Gombo)", "Sauce graine de palme, gombo, crevettes, riz", 4500),
    ("Plats Principaux", "Foutou + Sauce Clair", "Pate d'igname, sauce claire tomate, poisson", 4000),
    ("Plats Principaux", "Placali + Sauce Gombo", "Pate de manioc fermentee, sauce gombo, poisson fume", 4000),
    ("Plats Principaux", "Riz Sauce Tomate", "Riz blanc, sauce tomate relevee, poulet braise, plantain frit", 4500),
    ("Plats Principaux", "Attieke Poulet", "Attieke, poulet braise, oignon, tomate, sauce piment", 4000),
    ("Grillades & Poisson", "Poulet Braise", "Poulet fermier marine, braise au charbon, sauce piment", 6000),
    ("Grillades & Poisson", "Poisson Braise (Capitaine)", "Capitaine frais, braise, sauce oignon-tomate-piment", 8000),
    ("Grillades & Poisson", "Maquereau Grilles", "2 maquereaux marines, grilles, sauce gboma", 4500),
    ("Grillades & Poisson", "Mouton Braise", "Mouton tendre marine, braise, epices", 7500),
    ("Grillades & Poisson", "Cotelettes d'Agneau", "Cotelettes grillees, herbes, beurre d'ail", 7000),
    ("Accompagnements", "Riz Blanc", "Riz parfume cuit a la vapeur", 1000),
    ("Accompagnements", "Frites de Patate Douce", "Patate douce frite, epices douces", 1500),
    ("Accompagnements", "Alloco (Banane Plantain Frite)", "Banane plantain frite doree", 1500),
    ("Accompagnements", "Legumes Sautes", "Haricots verts, carotte, chou, poivron", 1500),
    ("Desserts", "Creme Caramel Maison", "Creme caramel onctueuse, vanille naturelle", 2000),
    ("Desserts", "Salade de Fruits Frais", "Fruits de saison coupes, sirop leger, menthe", 2500),
    ("Desserts", "Mousse au Chocolat", "Mousse chocolat noir 70%, chantilly", 2500),
    ("Desserts", "Beignets de Banane", "Beignets sucres, cannelle, sucre glace", 2000),
    ("Desserts", "Gateau a la Mangue", "Gateau moelleux mangue, glacage fruit de la passion", 3000),
    ("Boissons Fraiches", "Jus de Bissap (Hibiscus)", "Bissap frais, menthe, gingembre", 1500),
    ("Boissons Fraiches", "Jus de Gingembre", "Gingembre frais rape, citron, miel", 1500),
    ("Boissons Fraiches", "Jus de Tamarin", "Tamarin nature, sucre de canne", 1500),
    ("Boissons Fraiches", "Cocktail Maison", "Mangue, ananas, orange, gingembre", 2500),
    ("Boissons Fraiches", "Eau Minerale 75cl", "Eau de source", 1000),
    ("Boissons Fraiches", "Boisson Gazeuse (Canette)", "Coca, Fanta, Sprite 33cl", 1000),
    ("Boissons Chaudes", "Cafe Expresso", "Cafe pur arabica", 1000),
    ("Boissons Chaudes", "Cafe Touba", "Cafe epice au poivre de Guinee", 1200),
    ("Boissons Chaudes", "The a la Menthe", "The vert, menthe fraiche, sucre", 1000),
    ("Boissons Chaudes", "Chocolat Chaud", "Chocolat noir, lait entier, cannelle", 1500),
    ("Boissons Chaudes", "Infusion Maison", "Citronnelle, gingembre, miel", 1000),
]

IMG = "https://picsum.photos/seed"

def main():
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT id, nom FROM etablissements WHERE nom LIKE '%Restaurant%' OR nom LIKE '%Republique%' LIMIT 1")
    existing = cur.fetchone()
    if existing:
        log.info(f"Etablissement existe deja : {existing['nom']}")
        eid = existing['id']
        # Nettoyer dans l'ordre des FK
        cur.execute("DELETE FROM mouvements_stock WHERE produit_id IN (SELECT id FROM produits WHERE etablissement_id = %s)", (eid,))
        cur.execute("DELETE FROM lignes_commande WHERE commande_id IN (SELECT id FROM commandes WHERE etablissement_id = %s)", (eid,))
        cur.execute("DELETE FROM commandes WHERE etablissement_id = %s", (eid,))
        cur.execute("DELETE FROM factures WHERE commande_id IN (SELECT id FROM commandes WHERE etablissement_id = %s)", (eid,))
        cur.execute("DELETE FROM evaluations WHERE produit_id IN (SELECT id FROM produits WHERE etablissement_id = %s)", (eid,))
        cur.execute("DELETE FROM activation_codes WHERE cree_par IN (SELECT id FROM utilisateurs WHERE etablissement_id = %s)", (eid,))
        cur.execute("DELETE FROM devices WHERE utilisateur_id IN (SELECT id FROM utilisateurs WHERE etablissement_id = %s)", (eid,))
        cur.execute("DELETE FROM faqs WHERE etablissement_id = %s", (eid,))
        cur.execute("DELETE FROM produits WHERE etablissement_id = %s", (eid,))
        cur.execute("DELETE FROM categories WHERE etablissement_id = %s", (eid,))
        cur.execute("DELETE FROM utilisateurs WHERE etablissement_id = %s", (eid,))
        cur.execute("DELETE FROM etablissements WHERE id = %s", (eid,))
        conn.commit()
        log.info("Anciennes donnees nettoyees.")

    # Établissement
    log.info("Creation etablissement...")
    cur.execute("""
        INSERT INTO etablissements (id, nom, type, historique, mission,
            adresse, horaires, telephone, email, site_web, reseaux_sociaux,
            taux_tva_defaut, moyens_paiement_acceptes, created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (ETAB_ID,
        "Restaurant La Republique", "restaurant",
        "Fonde en 2010, le Restaurant La Republique est une reference "
        "de la cuisine africaine contemporaine a Lome.",
        "Offrir une experience culinaire authentique celebrant la richesse "
        "des traditions gastronomiques de l'Afrique de l'Ouest.",
        "123 Avenue de la Republique, Lome, Togo",
        '{"lundi":"11h-22h","mardi":"11h-22h","mercredi":"11h-22h",'
        '"jeudi":"11h-23h","vendredi":"11h-23h","samedi":"17h-23h30",'
        '"dimanche":"12h-21h"}',
        "+228 90 00 00 01", "contact@larepublique.tg",
        "https://larepublique.tg",
        '{"facebook":"LaRepubliqueLome","instagram":"larepublique_tg"}',
        18, "Carte, Especes, TMoney, Flooz", ADMIN_ID))

    # Admin
    from apps.common.auth import AuthManager
    auth = AuthManager(conn)
    cur.execute("SELECT id FROM roles WHERE nom='admin'")
    role = cur.fetchone()
    if role:
        h = auth.hash_password("admin123")
        cur.execute("""
            INSERT INTO utilisateurs (id, etablissement_id, nom, email,
                role_id, password_hash, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO NOTHING
        """, (ADMIN_ID, ETAB_ID, "Patrice", "admin@larepublique.tg",
              role["id"], h, ADMIN_ID))
        log.info("Admin : admin@larepublique.tg / admin123")

    # Catégories
    log.info("Categories...")
    cat_map = {}
    for nom, ico in CATS:
        cid = uid()
        cat_map[nom] = cid
        cur.execute("""
            INSERT INTO categories (id, nom, icone, etablissement_id, created_by)
            VALUES (%s,%s,%s,%s,%s)
        """, (cid, nom, ico, ETAB_ID, ADMIN_ID))

    # Produits
    log.info("Produits...")
    for i, (cn, nom, desc, prix) in enumerate(PLATS):
        cid = cat_map.get(cn)
        if not cid:
            continue
        pid = uid()
        cur.execute("""
            INSERT INTO produits (id, categorie_id, nom, description, photo_url,
                prix, taux_tva, stock, stock_alerte, permets_commande,
                etablissement_id, created_by, updated_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (pid, cid, nom, desc, f"{IMG}/{pid[:8]}/400/300",
              prix, 0, 10, 5, True, ETAB_ID, ADMIN_ID, ADMIN_ID))

    conn.commit()
    cur.close()
    log.info("Termine.")
    print("\n=== Base remplie ===")
    print("Email: admin@larepublique.tg")
    print("Mdp: admin123")
    print("Lancez: python -m apps.admin")

if __name__ == "__main__":
    main()
    conn.close()
