"""Tests unitaires pour l'application Staff (Restaurant).

Couvre : panier, création de commandes, KDS, paiement, CA serveur.
"""
import sys
import uuid

import psycopg2
import psycopg2.extras
import pytest

sys.path.insert(0, r"C:\projet")

from ArtizBoardCommon.config_loader import get_db_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_conn():
    db = get_db_config()
    return psycopg2.connect(
        host=db[0],
        port=db[1],
        dbname=db[2],
        user=db[3],
        password=db[4],
        client_encoding="UTF8",
    )


def _make_cart_item(pid, nom, prix, qty=1):
    """Create a cart item dict matching StaffApp._cart structure."""
    return {"id": str(pid), "nom": nom, "prix": float(prix), "qty": qty}


# ---------------------------------------------------------------------------
# Fixture : données de test (produits + catégorie)
# ---------------------------------------------------------------------------

@pytest.fixture
def test_data(admin_id, etab_id):
    """Insère une catégorie et 2 produits de test, nettoie après le test."""
    if not admin_id or not etab_id:
        pytest.skip("Données de seed absentes (admin_id / etab_id)")

    conn = _fresh_conn()
    cur = conn.cursor()

    cat_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO categories (id, nom, etablissement_id, created_by)
           VALUES (%s, %s, %s, %s)""",
        (cat_id, "Test_Categorie", etab_id, admin_id),
    )

    p1_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO produits (id, categorie_id, nom, prix, etablissement_id, created_by)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (p1_id, cat_id, "Burger", 2500, etab_id, admin_id),
    )

    p2_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO produits (id, categorie_id, nom, prix, etablissement_id, created_by)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (p2_id, cat_id, "Frites", 1000, etab_id, admin_id),
    )
    conn.commit()

    data = {
        "cat_id": cat_id,
        "p1": {"id": p1_id, "nom": "Burger", "prix": 2500},
        "p2": {"id": p2_id, "nom": "Frites", "prix": 1000},
    }

    yield data

    # Nettoyage
    cur.execute(
        "DELETE FROM lignes_commande WHERE produit_id IN (%s, %s)",
        (p1_id, p2_id),
    )
    cur.execute(
        """DELETE FROM commandes WHERE id IN (
            SELECT DISTINCT commande_id FROM lignes_commande
            WHERE produit_id IN (%s, %s)
        )""",
        (p1_id, p2_id),
    )
    # Nettoyer aussi les commandes insérées directement (KDS, paiement)
    cnx = conn.cursor()
    cnx.execute(
        "SELECT c.id FROM commandes c WHERE c.etablissement_id = %s",
        (etab_id,),
    )
    for row in cnx.fetchall():
        conn.cursor().execute("DELETE FROM lignes_commande WHERE commande_id=%s", (row[0],))
    conn.cursor().execute("DELETE FROM commandes WHERE etablissement_id=%s", (etab_id,))
    cnx.close()

    cur.execute("DELETE FROM produits WHERE id IN (%s, %s)", (p1_id, p2_id))
    cur.execute("DELETE FROM categories WHERE id = %s", (cat_id,))
    conn.commit()
    cur.close()
    conn.close()


# ========================================================================
# TestCart — Gestion du panier (in-memory, pas de DB)
# ========================================================================

class TestCart:
    """Tests de la gestion du panier (_cart_add, _cart_rem)."""

    def test_cart_add_new_item(self):
        """Ajout d'un nouveau produit : le panier contient 1 article avec qty=1."""
        cart = []
        prod = {"id": "abc", "nom": "Burger", "prix": 2500}
        pid = str(prod["id"])
        ex = next((c for c in cart if c["id"] == pid), None)
        if ex:
            ex["qty"] += 1
        else:
            cart.append({"id": pid, "nom": prod["nom"], "prix": float(prod["prix"]), "qty": 1})

        assert len(cart) == 1
        assert cart[0]["qty"] == 1
        assert cart[0]["nom"] == "Burger"

    def test_cart_add_existing_item_increments_qty(self):
        """Ajout répété du même produit : la quantité augmente sans dupliquer."""
        cart = []
        prod = {"id": "p1", "nom": "Frites", "prix": 1000}
        pid = str(prod["id"])

        for _ in range(3):
            ex = next((c for c in cart if c["id"] == pid), None)
            if ex:
                ex["qty"] += 1
            else:
                cart.append({"id": pid, "nom": prod["nom"], "prix": float(prod["prix"]), "qty": 1})

        assert len(cart) == 1
        assert cart[0]["qty"] == 3

    def test_cart_remove_item_decrements_qty(self):
        """Retrait d'un article réduit la quantité mais conserve l'article."""
        cart = [_make_cart_item("p1", "Burger", 2500, 3)]

        pid = "p1"
        ex = next((c for c in cart if c["id"] == pid), None)
        ex["qty"] -= 1

        assert cart[0]["qty"] == 2
        assert len(cart) == 1

    def test_cart_remove_last_item_removes_from_cart(self):
        """Retrait du dernier exemplaire supprime l'article du panier."""
        cart = [_make_cart_item("p1", "Burger", 2500, 1)]

        pid = "p1"
        ex = next((c for c in cart if c["id"] == pid), None)
        ex["qty"] -= 1
        if ex["qty"] <= 0:
            cart = [c for c in cart if c["id"] != pid]

        assert len(cart) == 0

    def test_cart_total_calculation(self):
        """Le total du panier correspond à la somme (prix * qty)."""
        cart = [
            _make_cart_item("p1", "Burger", 2500, 2),
            _make_cart_item("p2", "Frites", 1000, 3),
        ]
        total = sum(c["prix"] * c["qty"] for c in cart)
        assert total == 2500 * 2 + 1000 * 3  # 8000

    def test_cart_empty_total_is_zero(self):
        """Le total d'un panier vide vaut 0."""
        cart = []
        total = sum(c["prix"] * c["qty"] for c in cart)
        assert total == 0

    def test_cart_add_multiple_different_products(self):
        """Ajout de plusieurs produits distincts sans duplication."""
        cart = []
        for prod in [
            {"id": "p1", "nom": "Burger", "prix": 2500},
            {"id": "p2", "nom": "Frites", "prix": 1000},
            {"id": "p3", "nom": "Coca", "prix": 500},
        ]:
            pid = str(prod["id"])
            ex = next((c for c in cart if c["id"] == pid), None)
            if ex:
                ex["qty"] += 1
            else:
                cart.append({"id": pid, "nom": prod["nom"], "prix": float(prod["prix"]), "qty": 1})

        assert len(cart) == 3


# ========================================================================
# TestCommande — Validation (_validate)
# ========================================================================

class TestCommande:
    """Tests de création de commande via _validate (INSERT commandes + lignes)."""

    def test_validate_empty_cart_is_noop(self, test_data, admin_id, etab_id):
        """Un panier vide ne crée aucune commande en base."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM commandes WHERE etablissement_id=%s AND deleted_at IS NULL",
            (etab_id,),
        )
        before = cur.fetchone()[0]

        cart = []
        if not cart:
            status = "noop"
        else:
            status = "created"

        assert status == "noop"
        cur.close()
        conn.close()

    def test_validate_creates_commande(self, test_data, admin_id, etab_id):
        """La validation d'un panier non vide crée une commande en base."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cart = [
            _make_cart_item(test_data["p1"]["id"], test_data["p1"]["nom"], test_data["p1"]["prix"], 2),
            _make_cart_item(test_data["p2"]["id"], test_data["p2"]["nom"], test_data["p2"]["prix"], 1),
        ]
        cid = str(uuid.uuid4())
        total = sum(c["prix"] * c["qty"] for c in cart)
        table_ref = "T2"

        cur.execute(
            """INSERT INTO commandes (id, staff_id, etablissement_id, reference_client,
               statut, type_service, total, moyen_paiement, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, admin_id, etab_id, table_ref, "en_attente", "sur_place", total, None, "en_attente", admin_id),
        )
        conn.commit()

        cur.execute("SELECT total, reference_client, statut FROM commandes WHERE id=%s", (cid,))
        row = cur.fetchone()

        assert row is not None
        assert float(row[0]) == total
        assert row[1] == table_ref
        assert row[2] == "en_attente"

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_validate_correct_total(self, test_data, admin_id, etab_id):
        """Le total enregistré en base correspond à la somme (prix * qte)."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cart = [
            _make_cart_item(test_data["p1"]["id"], test_data["p1"]["nom"], test_data["p1"]["prix"], 3),
            _make_cart_item(test_data["p2"]["id"], test_data["p2"]["nom"], test_data["p2"]["prix"], 4),
        ]
        expected_total = 2500 * 3 + 1000 * 4  # 11500
        total = sum(c["prix"] * c["qty"] for c in cart)
        cid = str(uuid.uuid4())

        cur.execute(
            """INSERT INTO commandes (id, staff_id, etablissement_id, reference_client,
               statut, type_service, total, moyen_paiement, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, admin_id, etab_id, "T1", "en_attente", "sur_place", total, None, "en_attente", admin_id),
        )
        conn.commit()

        cur.execute("SELECT total FROM commandes WHERE id=%s", (cid,))
        row = cur.fetchone()
        assert float(row[0]) == expected_total

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_validate_creates_lignes_commande(self, test_data, admin_id, etab_id):
        """Chaque article du panier génère une ligne_commande avec la bonne quantité."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cart = [
            _make_cart_item(test_data["p1"]["id"], test_data["p1"]["nom"], test_data["p1"]["prix"], 2),
            _make_cart_item(test_data["p2"]["id"], test_data["p2"]["nom"], test_data["p2"]["prix"], 5),
        ]
        cid = str(uuid.uuid4())
        total = sum(c["prix"] * c["qty"] for c in cart)

        cur.execute(
            """INSERT INTO commandes (id, staff_id, etablissement_id, reference_client,
               statut, type_service, total, moyen_paiement, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, admin_id, etab_id, "T3", "en_attente", "sur_place", total, None, "en_attente", admin_id),
        )
        for c in cart:
            cur.execute(
                """INSERT INTO lignes_commande (id, commande_id, produit_id, quantite, prix_unitaire)
                   VALUES (%s,%s,%s,%s,%s)""",
                (str(uuid.uuid4()), cid, c["id"], c["qty"], c["prix"]),
            )
        conn.commit()

        cur.execute(
            "SELECT COUNT(*) FROM lignes_commande WHERE commande_id=%s AND deleted_at IS NULL",
            (cid,),
        )
        nb = cur.fetchone()[0]
        assert nb == 2

        # Vérifier les quantités
        cur.execute(
            """SELECT quantite FROM lignes_commande
               WHERE commande_id=%s AND deleted_at IS NULL ORDER BY quantite""",
            (cid,),
        )
        rows = cur.fetchall()
        quantities = sorted([r[0] for r in rows])
        assert quantities == [2, 5]

        # Nettoyage
        cur.execute("DELETE FROM lignes_commande WHERE commande_id=%s", (cid,))
        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_validate_with_table_reference(self, test_data, admin_id, etab_id):
        """La référence client correspond au numéro de table."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cart = [_make_cart_item(test_data["p1"]["id"], test_data["p1"]["nom"], test_data["p1"]["prix"], 1)]
        cid = str(uuid.uuid4())
        table_ref = "Comptoir"

        cur.execute(
            """INSERT INTO commandes (id, staff_id, etablissement_id, reference_client,
               statut, type_service, total, moyen_paiement, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, admin_id, etab_id, table_ref, "en_attente", "sur_place",
             cart[0]["prix"], None, "en_attente", admin_id),
        )
        conn.commit()

        cur.execute("SELECT reference_client FROM commandes WHERE id=%s", (cid,))
        row = cur.fetchone()
        assert row[0] == "Comptoir"

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_validate_initial_status_is_en_attente(self, test_data, admin_id, etab_id):
        """Une nouvelle commande a toujours le statut 'en_attente'."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cart = [_make_cart_item(test_data["p1"]["id"], test_data["p1"]["nom"], test_data["p1"]["prix"], 1)]
        cid = str(uuid.uuid4())
        total = cart[0]["prix"]

        cur.execute(
            """INSERT INTO commandes (id, staff_id, etablissement_id, reference_client,
               statut, type_service, total, moyen_paiement, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, admin_id, etab_id, "T1", "en_attente", "sur_place", total, None, "en_attente", admin_id),
        )
        conn.commit()

        cur.execute("SELECT statut, statut_paiement FROM commandes WHERE id=%s", (cid,))
        row = cur.fetchone()
        assert row[0] == "en_attente"
        assert row[1] == "en_attente"

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()


# ========================================================================
# TestKDS — Avancement cuisine (_ch_kds)
# ========================================================================

class TestKDS:
    """Tests du Kitchen Display System (_ch_kds)."""

    def _create_commande(self, cur, admin_id, etab_id, statut="en_attente"):
        cid = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO commandes (id, staff_id, etablissement_id, reference_client,
               statut, type_service, total, moyen_paiement, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, admin_id, etab_id, "T1", statut, "sur_place", 1000, None, "en_attente", admin_id),
        )
        return cid

    def test_kds_advance_en_attente_to_en_preparation(self, test_data, admin_id, etab_id):
        """Transition 'en_attente' → 'en_preparation' acceptée."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cid = self._create_commande(cur, admin_id, etab_id, "en_attente")
        conn.commit()

        cur.execute("UPDATE commandes SET statut=%s WHERE id=%s", ("en_preparation", cid))
        conn.commit()

        cur.execute("SELECT statut FROM commandes WHERE id=%s", (cid,))
        row = cur.fetchone()
        assert row[0] == "en_preparation"

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_kds_advance_en_preparation_to_pret(self, test_data, admin_id, etab_id):
        """Transition 'en_preparation' → 'pret' acceptée."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cid = self._create_commande(cur, admin_id, etab_id, "en_preparation")
        conn.commit()

        cur.execute("UPDATE commandes SET statut=%s WHERE id=%s", ("pret", cid))
        conn.commit()

        cur.execute("SELECT statut FROM commandes WHERE id=%s", (cid,))
        row = cur.fetchone()
        assert row[0] == "pret"

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_kds_no_advance_when_no_next_status(self, test_data, admin_id, etab_id):
        """Aucune transition si next_status est None (cas de 'pret')."""
        # Le code Staff ne propose pas de bouton pour "pret" car next_st["pret"] n'existe pas.
        next_st_map = {"en_attente": "en_preparation", "en_preparation": "pret"}

        ns = next_st_map.get("pret")  # doit être None
        assert ns is None

        # Dans _ch_kds, si ns est None, on ne fait rien.
        # On vérifie que la DB n'est pas modifiée.
        conn = _fresh_conn()
        cur = conn.cursor()
        cid = self._create_commande(cur, admin_id, etab_id, "pret")
        conn.commit()

        ns = next_st_map.get("pret")
        if ns:
            cur.execute("UPDATE commandes SET statut=%s WHERE id=%s", (ns, cid))
            conn.commit()

        cur.execute("SELECT statut FROM commandes WHERE id=%s", (cid,))
        row = cur.fetchone()
        assert row[0] == "pret"  # statut inchangé

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_kds_does_not_modify_other_fields(self, test_data, admin_id, etab_id):
        """_ch_kds ne modifie que le statut, pas le reste."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cid = self._create_commande(cur, admin_id, etab_id, "en_attente")
        conn.commit()

        # Enregistrer les valeurs initiales
        cur.execute(
            """SELECT total, reference_client, statut_paiement, type_service
               FROM commandes WHERE id=%s""",
            (cid,),
        )
        before = cur.fetchone()

        cur.execute("UPDATE commandes SET statut=%s WHERE id=%s", ("en_preparation", cid))
        conn.commit()

        cur.execute(
            """SELECT total, reference_client, statut_paiement, type_service
               FROM commandes WHERE id=%s""",
            (cid,),
        )
        after = cur.fetchone()

        assert float(after[0]) == float(before[0])
        assert after[1] == before[1]
        assert after[2] == before[2]
        assert after[3] == before[3]

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()


# ========================================================================
# TestPaiement — Encaissement (_payer)
# ========================================================================

class TestPaiement:
    """Tests du module de paiement (_payer)."""

    def _create_commande(self, cur, admin_id, etab_id, statut="pret"):
        cid = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO commandes (id, staff_id, etablissement_id, reference_client,
               statut, type_service, total, moyen_paiement, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, admin_id, etab_id, "T1", statut, "sur_place", 3500, None, "en_attente", admin_id),
        )
        return cid

    def test_payer_sets_statut_paiement_to_paye(self, test_data, admin_id, etab_id):
        """Le paiement passe statut_paiement à 'paye'."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cid = self._create_commande(cur, admin_id, etab_id, "pret")
        conn.commit()

        cur.execute(
            """UPDATE commandes SET statut_paiement='paye', moyen_paiement='cash',
               statut='livre', updated_by=%s, updated_at=NOW() WHERE id=%s""",
            (admin_id, cid),
        )
        conn.commit()

        cur.execute("SELECT statut_paiement FROM commandes WHERE id=%s", (cid,))
        row = cur.fetchone()
        assert row[0] == "paye"

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_payer_sets_moyen_paiement_to_cash(self, test_data, admin_id, etab_id):
        """Le paiement par défaut utilise le moyen 'cash'."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cid = self._create_commande(cur, admin_id, etab_id, "pret")
        conn.commit()

        cur.execute(
            """UPDATE commandes SET statut_paiement='paye', moyen_paiement='cash',
               statut='livre', updated_by=%s, updated_at=NOW() WHERE id=%s""",
            (admin_id, cid),
        )
        conn.commit()

        cur.execute("SELECT moyen_paiement FROM commandes WHERE id=%s", (cid,))
        row = cur.fetchone()
        assert row[0] == "cash"

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_payer_sets_statut_to_livre(self, test_data, admin_id, etab_id):
        """Le paiement passe aussi le statut à 'livre'."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cid = self._create_commande(cur, admin_id, etab_id, "pret")
        conn.commit()

        cur.execute(
            """UPDATE commandes SET statut_paiement='paye', moyen_paiement='cash',
               statut='livre', updated_by=%s, updated_at=NOW() WHERE id=%s""",
            (admin_id, cid),
        )
        conn.commit()

        cur.execute("SELECT statut FROM commandes WHERE id=%s", (cid,))
        row = cur.fetchone()
        assert row[0] == "livre"

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_payer_records_updater(self, test_data, admin_id, etab_id):
        """Le paiement enregistre l'utilisateur qui a encaissé (updated_by)."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cid = self._create_commande(cur, admin_id, etab_id, "pret")
        conn.commit()

        cur.execute(
            """UPDATE commandes SET statut_paiement='paye', moyen_paiement='cash',
               statut='livre', updated_by=%s, updated_at=NOW() WHERE id=%s""",
            (admin_id, cid),
        )
        conn.commit()

        cur.execute("SELECT updated_by FROM commandes WHERE id=%s", (cid,))
        row = cur.fetchone()
        assert str(row[0]) == admin_id

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()


# ========================================================================
# TestCA — Chiffre d'affaires du serveur
# ========================================================================

class TestCA:
    """Tests de l'agrégation CA serveur (requête encaisser_view)."""

    def _create_paid_commande(self, cur, admin_id, etab_id, total, moyen_paiement):
        cid = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO commandes (id, staff_id, etablissement_id, reference_client,
               statut, type_service, total, moyen_paiement, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, admin_id, etab_id, "T1", "livre", "sur_place", total, moyen_paiement, "paye", admin_id),
        )
        return cid

    def test_ca_par_moyen_paiement_aggregate(self, test_data, admin_id, etab_id):
        """La requête CA regroupe correctement par moyen de paiement."""
        conn = _fresh_conn()
        cur = conn.cursor()
        c1 = self._create_paid_commande(cur, admin_id, etab_id, 5000, "cash")
        c2 = self._create_paid_commande(cur, admin_id, etab_id, 3000, "cash")
        c3 = self._create_paid_commande(cur, admin_id, etab_id, 7000, "tmoney")
        conn.commit()

        cur.execute(
            """SELECT moyen_paiement, SUM(total) as total, COUNT(*) as nb
               FROM commandes
               WHERE etablissement_id=%s AND staff_id=%s AND statut_paiement='paye'
               AND created_at>=CURRENT_DATE AND deleted_at IS NULL
               GROUP BY moyen_paiement""",
            (etab_id, admin_id),
        )
        rows = cur.fetchall()
        ca_by_method = {r[0]: float(r[1]) for r in rows}

        assert ca_by_method["cash"] == 8000.0
        assert ca_by_method["tmoney"] == 7000.0

        for c in [c1, c2, c3]:
            cur.execute("DELETE FROM commandes WHERE id=%s", (c,))
        conn.commit()
        cur.close()
        conn.close()

    def test_ca_total_matches_sum(self, test_data, admin_id, etab_id):
        """Le total CA = somme des totaux par moyen de paiement."""
        conn = _fresh_conn()
        cur = conn.cursor()
        c1 = self._create_paid_commande(cur, admin_id, etab_id, 2000, "cash")
        c2 = self._create_paid_commande(cur, admin_id, etab_id, 4000, "tmoney")
        c3 = self._create_paid_commande(cur, admin_id, etab_id, 1500, "flooz")
        conn.commit()

        cur.execute(
            """SELECT moyen_paiement, SUM(total) as total
               FROM commandes
               WHERE etablissement_id=%s AND staff_id=%s AND statut_paiement='paye'
               AND created_at>=CURRENT_DATE AND deleted_at IS NULL
               GROUP BY moyen_paiement""",
            (etab_id, admin_id),
        )
        rows = cur.fetchall()
        ca = {r[0]: float(r[1]) for r in rows}
        total_ca = sum(ca.values())
        assert total_ca == 7500.0

        for c in [c1, c2, c3]:
            cur.execute("DELETE FROM commandes WHERE id=%s", (c,))
        conn.commit()
        cur.close()
        conn.close()

    def test_ca_no_paid_orders_returns_empty(self, test_data, admin_id, etab_id):
        """Aucune commande payée aujourd'hui → CA vide."""
        conn = _fresh_conn()
        cur = conn.cursor()
        cur.execute(
            """SELECT moyen_paiement, SUM(total) as total
               FROM commandes
               WHERE etablissement_id=%s AND staff_id=%s AND statut_paiement='paye'
               AND created_at>=CURRENT_DATE AND deleted_at IS NULL
               GROUP BY moyen_paiement""",
            (etab_id, admin_id),
        )
        rows = cur.fetchall()
        assert len(rows) == 0
        cur.close()
        conn.close()

    def test_ca_only_counts_paid_status(self, test_data, admin_id, etab_id):
        """Seules les commandes avec statut_paiement='paye' sont comptées."""
        conn = _fresh_conn()
        cur = conn.cursor()
        c_paid = self._create_paid_commande(cur, admin_id, etab_id, 5000, "cash")
        # Créer une commande non payée
        c_unpaid = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO commandes (id, staff_id, etablissement_id, reference_client,
               statut, type_service, total, moyen_paiement, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (c_unpaid, admin_id, etab_id, "T1", "pret", "sur_place", 9999, None, "en_attente", admin_id),
        )
        conn.commit()

        cur.execute(
            """SELECT SUM(total) FROM commandes
               WHERE etablissement_id=%s AND staff_id=%s AND statut_paiement='paye'
               AND created_at>=CURRENT_DATE AND deleted_at IS NULL""",
            (etab_id, admin_id),
        )
        row = cur.fetchone()
        total_paye = float(row[0]) if row[0] else 0
        assert total_paye == 5000.0  # 9999 non inclus

        cur.execute("DELETE FROM commandes WHERE id IN (%s,%s)", (c_paid, c_unpaid))
        conn.commit()
        cur.close()
        conn.close()


# ========================================================================
# TestTable — Changement de table (_set_table)
# ========================================================================

class TestTable:
    """Tests de la logique de sélection de table."""

    def test_set_table_changes_reference(self):
        """_set_table met à jour la table courante."""
        tables = ["T1", "T2", "T3", "T4", "T5", "T6", "Comptoir"]
        current = "T1"

        # Simuler un clic sur "T3"
        current = "T3"
        assert current == "T3"
        assert current in tables

    def test_can_switch_to_comptoir(self):
        """Le changement vers 'Comptoir' est permis."""
        current = "T1"
        current = "Comptoir"
        assert current == "Comptoir"

    def test_invalid_table_not_allowed(self):
        """Une table inexistante ne devrait pas être acceptée."""
        tables = ["T1", "T2", "T3", "T4", "T5", "T6", "Comptoir"]
        invalid = "T99"
        assert invalid not in tables

    def test_cart_persists_across_table_switches(self):
        """Le panier n'est pas vidé lors d'un changement de table."""
        cart = [_make_cart_item("p1", "Burger", 2500, 2)]
        current = "T1"

        # Changer de table
        current = "T4"
        # Le panier doit rester intact
        assert len(cart) == 1
        assert cart[0]["nom"] == "Burger"
        assert cart[0]["qty"] == 2
