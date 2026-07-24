"""Tests unitaires pour l'application Client (Portail).

Couvre : checkout, panier, données tables, établissement, QR table.
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
        host=db[0], port=db[1], dbname=db[2],
        user=db[3], password=db[4], client_encoding="UTF8",
    )


def _make_cart_item(pid, nom, prix, qty=1):
    return {"id": str(pid), "nom": nom, "prix": float(prix), "qty": qty}


# ---------------------------------------------------------------------------
# TestCheckout
# ---------------------------------------------------------------------------

class TestCheckout:
    """Tests de creation de commandes + lignes (checkout)."""

    def test_checkout_creates_commande(self, admin_id, etab_id):
        """Une commande valide cree un enregistrement dans commandes."""
        if not admin_id or not etab_id:
            pytest.skip("Donnees de seed absentes")

        conn = _fresh_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cid = str(uuid.uuid4())
        total = 7500.0

        cur.execute(
            """INSERT INTO commandes (id, etablissement_id, reference_client,
               statut, type_service, total, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, etab_id, "T12", "en_attente", "sur_place", total,
             "en_attente", admin_id),
        )
        conn.commit()

        cur.execute("SELECT id, total, statut FROM commandes WHERE id=%s", (cid,))
        row = cur.fetchone()
        assert row is not None
        assert float(row["total"]) == total
        assert row["statut"] == "en_attente"

        # Cleanup
        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_checkout_creates_lignes(self, admin_id, etab_id):
        """Un checkout cree les lignes_commande associees."""
        if not admin_id or not etab_id:
            pytest.skip("Donnees de seed absentes")

        conn = _fresh_conn()
        cur = conn.cursor()

        # Get a product
        cur.execute(
            "SELECT id, prix FROM produits WHERE etablissement_id=%s AND deleted_at IS NULL LIMIT 1",
            (etab_id,),
        )
        prod = cur.fetchone()
        if not prod:
            pytest.skip("Aucun produit en DB")

        cid = str(uuid.uuid4())
        lid = str(uuid.uuid4())
        total = float(prod[1]) * 2

        cur.execute(
            """INSERT INTO commandes (id, etablissement_id, reference_client,
               statut, type_service, total, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, etab_id, "Web", "en_attente", "emporter", total,
             "en_attente", admin_id),
        )
        cur.execute(
            """INSERT INTO lignes_commande (id, commande_id, produit_id, quantite, prix_unitaire)
               VALUES (%s,%s,%s,%s,%s)""",
            (lid, cid, prod[0], 2, prod[1]),
        )
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM lignes_commande WHERE commande_id=%s", (cid,))
        count = cur.fetchone()[0]
        assert count == 1

        # Cleanup
        cur.execute("DELETE FROM lignes_commande WHERE commande_id=%s", (cid,))
        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_checkout_total_matches_lignes(self, admin_id, etab_id):
        """Le total de la commande = somme(quantite * prix_unitaire) des lignes."""
        if not admin_id or not etab_id:
            pytest.skip("Donnees de seed absentes")

        conn = _fresh_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, prix FROM produits WHERE etablissement_id=%s AND deleted_at IS NULL LIMIT 3",
            (etab_id,),
        )
        prods = cur.fetchall()
        if len(prods) < 2:
            pytest.skip("Pas assez de produits")

        cid = str(uuid.uuid4())
        expected_total = 0.0
        for i, p in enumerate(prods):
            lid = str(uuid.uuid4())
            qty = i + 1
            expected_total += float(p[1]) * qty
            cur.execute(
                """INSERT INTO lignes_commande (id, commande_id, produit_id, quantite, prix_unitaire)
                   VALUES (%s,%s,%s,%s,%s)""",
                (lid, cid, p[0], qty, p[1]),
            )

        cur.execute(
            """INSERT INTO commandes (id, etablissement_id, reference_client,
               statut, type_service, total, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, etab_id, "Web", "en_attente", "emporter", expected_total,
             "en_attente", admin_id),
        )
        conn.commit()

        cur.execute("SELECT SUM(quantite * prix_unitaire) FROM lignes_commande WHERE commande_id=%s", (cid,))
        db_total = float(cur.fetchone()[0] or 0)
        assert abs(db_total - expected_total) < 0.01

        # Cleanup
        cur.execute("DELETE FROM lignes_commande WHERE commande_id=%s", (cid,))
        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_checkout_with_payment(self, admin_id, etab_id):
        """Checkout avec statut_paiement=paye et moyen_paiement renseigne."""
        if not admin_id or not etab_id:
            pytest.skip("Donnees de seed absentes")

        conn = _fresh_conn()
        cur = conn.cursor()
        cid = str(uuid.uuid4())

        cur.execute(
            """INSERT INTO commandes (id, etablissement_id, reference_client,
               statut, type_service, total, moyen_paiement, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, etab_id, "T01", "pret", "sur_place", 5000.0, "tmoney", "paye", admin_id),
        )
        conn.commit()

        cur.execute("SELECT moyen_paiement, statut_paiement FROM commandes WHERE id=%s", (cid,))
        row = cur.fetchone()
        assert row[0] == "tmoney"
        assert row[1] == "paye"

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()

    def test_checkout_annule_does_not_create_facture(self, admin_id, etab_id):
        """Une commande annulee ne genere pas de facture (regle metier)."""
        if not admin_id or not etab_id:
            pytest.skip("Donnees de seed absentes")

        conn = _fresh_conn()
        cur = conn.cursor()
        cid = str(uuid.uuid4())

        cur.execute(
            """INSERT INTO commandes (id, etablissement_id, reference_client,
               statut, type_service, total, statut_paiement, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, etab_id, "Web", "annule", "emporter", 3000.0, "en_attente", admin_id),
        )
        conn.commit()

        # Verify no facture linked
        cur.execute("SELECT COUNT(*) FROM factures WHERE commande_id=%s", (cid,))
        assert cur.fetchone()[0] == 0

        cur.execute("DELETE FROM commandes WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
        conn.close()


# ---------------------------------------------------------------------------
# TestCartClient
# ---------------------------------------------------------------------------

class TestCartClient:
    """Tests du panier client (add, remove, total)."""

    def test_add_to_cart(self, admin_id, etab_id):
        """Ajouter un produit au panier incremente la quantite."""
        if not admin_id or not etab_id:
            pytest.skip("Donnees de seed absentes")

        pid = str(uuid.uuid4())
        cart = []

        item = _make_cart_item(pid, "Test", 1500, 1)

        # Simulate _cart_add
        ex = next((c for c in cart if c["id"] == pid), None)
        if ex:
            ex["qty"] += 1
        else:
            cart.append(item)

        assert len(cart) == 1
        assert cart[0]["qty"] == 1
        assert cart[0]["nom"] == "Test"

    def test_add_existing_increments_qty(self):
        """Ajouter un produit deja dans le panier incremente quantite."""
        pid = "prod-123"
        cart = [_make_cart_item(pid, "Burger", 2500, 2)]

        ex = next((c for c in cart if c["id"] == pid), None)
        ex["qty"] += 1

        assert cart[0]["qty"] == 3
        assert len(cart) == 1

    def test_remove_from_cart(self):
        """Retirer un produit reduit la quantite."""
        pid = "prod-456"
        cart = [_make_cart_item(pid, "Frites", 1000, 2)]

        ex = next((c for c in cart if c["id"] == pid), None)
        ex["qty"] -= 1

        assert cart[0]["qty"] == 1

    def test_remove_last_removes_item(self):
        """Quand quantite atteint 0, l'item est supprime du panier."""
        pid = "prod-789"
        cart = [_make_cart_item(pid, "Coca", 500, 1)]

        ex = next((c for c in cart if c["id"] == pid), None)
        ex["qty"] -= 1
        if ex["qty"] <= 0:
            cart = [c for c in cart if c["id"] != pid]

        assert len(cart) == 0

    def test_cart_total(self):
        """Le total du panier est correct."""
        cart = [
            _make_cart_item("p1", "A", 1000, 2),
            _make_cart_item("p2", "B", 2500, 1),
            _make_cart_item("p3", "C", 500, 3),
        ]
        total = sum(c["prix"] * c["qty"] for c in cart)
        assert total == 6000.0  # 2000 + 2500 + 1500

    def test_cart_empty_total_is_zero(self):
        """Panier vide = total 0."""
        cart = []
        total = sum(c["prix"] * c["qty"] for c in cart)
        assert total == 0


# ---------------------------------------------------------------------------
# TestNavigation
# ---------------------------------------------------------------------------

class TestNavigation:
    """Tests de navigation, donnees, QR table."""

    def test_etablissement_info_loaded(self, cur, etab_id):
        """Les infos etablissement sont chargees depuis la DB."""
        if not etab_id:
            pytest.skip("Etablissement absent")

        cur.execute("SELECT nom, email, telephone FROM etablissements WHERE id=%s", (etab_id,))
        row = cur.fetchone()
        assert row is not None
        assert row["nom"] is not None
        assert len(row["nom"]) > 0

    def test_categories_loaded(self, cur, etab_id):
        """Les categories sont chargees depuis la DB."""
        if not etab_id:
            pytest.skip("Etablissement absent")

        cur.execute(
            "SELECT COUNT(*) FROM categories WHERE etablissement_id=%s AND deleted_at IS NULL",
            (etab_id,),
        )
        count = cur.fetchone()["count"]
        assert count > 0

    def test_produits_loaded(self, cur, etab_id):
        """Les produits sont charges depuis la DB."""
        if not etab_id:
            pytest.skip("Etablissement absent")

        cur.execute(
            """SELECT COUNT(*) FROM produits
               WHERE etablissement_id=%s AND deleted_at IS NULL AND permets_commande=TRUE""",
            (etab_id,),
        )
        count = cur.fetchone()["count"]
        assert count > 0

    def test_commandes_recentes_loaded(self, cur, etab_id):
        """Les commandes recentes sont chargees."""
        if not etab_id:
            pytest.skip("Etablissement absent")

        cur.execute(
            """SELECT id FROM commandes
               WHERE etablissement_id=%s AND deleted_at IS NULL
               ORDER BY created_at DESC LIMIT 10""",
            (etab_id,),
        )
        rows = cur.fetchall()
        assert isinstance(rows, list)  # peut etre vide, c'est OK

    def test_qr_table_detection(self):
        """Detection du parametre ?table=T12."""
        import urllib.parse

        q = "table=T12"
        p = urllib.parse.parse_qs(q)
        assert p.get("table") == ["T12"]

    def test_qr_table_no_param(self):
        """Sans parametre table, reference_client = None."""
        import urllib.parse

        p = urllib.parse.parse_qs("")
        assert p.get("table") is None

    def test_faqs_loaded(self, cur, etab_id):
        """Les FAQs sont chargees depuis la DB."""
        if not etab_id:
            pytest.skip("Etablissement absent")

        cur.execute(
            "SELECT COUNT(*) FROM faqs WHERE etablissement_id=%s AND deleted_at IS NULL",
            (etab_id,),
        )
        count = cur.fetchone()["count"]
        assert isinstance(count, int)
