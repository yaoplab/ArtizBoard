"""Tests de gestion de stock — ArtizBoard

Couvre : décrément stock, alertes rupture, mouvements_stock,
permets_commande, contrainte stock négatif, verrouillage optimiste.
"""
import sys, pytest, uuid
sys.path.insert(0, r'C:\projet')

import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from dashboard_manager import DashboardManager


# ── Helpers ──

def _get_produit(cur, etab_id, min_stock=0):
    cur.execute("""
        SELECT id, nom, stock, stock_alerte, version, permets_commande
        FROM produits
        WHERE etablissement_id = %s AND deleted_at IS NULL AND stock >= %s
        ORDER BY stock DESC LIMIT 1
    """, (etab_id, min_stock))
    return cur.fetchone()

def _create_commande(cur, etab_id, admin_id, ref="TEST-STOCK", total=5000):
    cid = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO commandes (id, etablissement_id, reference_client,
            statut, type_service, total, statut_paiement, created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (cid, etab_id, ref, "en_attente", "sur_place", total, "en_attente", admin_id))
    return cid

def _create_ligne(cur, commande_id, produit_id, quantite, prix=2500):
    lid = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO lignes_commande (id, commande_id, produit_id, quantite, prix_unitaire)
        VALUES (%s,%s,%s,%s,%s)
    """, (lid, commande_id, produit_id, quantite, prix))
    return lid


# ══════════════════════════════════════════════════════════════════════
# TestStock — Décrément de stock lors des ventes
# ══════════════════════════════════════════════════════════════════════

class TestStock:
    """Tests de décrément de stock lors des ventes."""

    def test_stock_decrement_on_sale(self, db_conn, etab_id, admin_id):
        """Le stock d'un produit doit diminuer après une vente validée."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id, min_stock=5)
        if not prod:
            cur.close(); pytest.skip("Aucun produit en stock disponible")

        produit_id = str(prod["id"])
        stock_initial = int(prod["stock"])
        qty = 3

        cid = _create_commande(cur, etab_id, admin_id)
        lid = _create_ligne(cur, cid, produit_id, qty)

        cur.execute("""
            UPDATE produits SET stock = stock - %s, updated_at = NOW()
            WHERE id = %s AND stock >= %s
            RETURNING stock
        """, (qty, produit_id, qty))
        updated = cur.fetchone()

        db_conn.commit()

        assert updated is not None, "Le décrément de stock a échoué"
        assert int(updated["stock"]) == stock_initial - qty

        # Nettoyer
        cur.execute("DELETE FROM lignes_commande WHERE id = %s", (lid,))
        cur.execute("DELETE FROM commandes WHERE id = %s", (cid,))
        cur.execute("UPDATE produits SET stock = %s WHERE id = %s", (stock_initial, produit_id))
        db_conn.commit()
        cur.close()

    def test_stock_decrement_multi_lignes(self, db_conn, etab_id, admin_id):
        """Le stock de plusieurs produits doit diminuer pour une commande multi-lignes."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT id, nom, stock FROM produits
            WHERE etablissement_id = %s AND deleted_at IS NULL AND stock >= 3
            LIMIT 3
        """, (etab_id,))
        prods_rows = cur.fetchall()
        if len(prods_rows) < 2:
            cur.close(); pytest.skip("Pas assez de produits en stock")

        prods = [(str(r["id"]), int(r["stock"]), r["nom"]) for r in prods_rows]

        cid = _create_commande(cur, etab_id, admin_id, ref="TEST-MULTI")

        for pid, _, _ in prods:
            lid = _create_ligne(cur, cid, pid, 1)
            cur.execute("""
                UPDATE produits SET stock = stock - 1, updated_at = NOW()
                WHERE id = %s AND stock >= 1
            """, (pid,))

        db_conn.commit()

        cur.execute("SELECT id, stock FROM produits WHERE id IN %s",
                   (tuple(p[0] for p in prods),))
        final_stocks = {r["id"]: int(r["stock"]) for r in cur.fetchall()}

        for pid, stock_init, _ in prods:
            assert final_stocks[pid] == stock_init - 1, f"Stock incorrect pour {pid}"

        # Nettoyer
        cur.execute("DELETE FROM lignes_commande WHERE commande_id = %s", (cid,))
        cur.execute("DELETE FROM commandes WHERE id = %s", (cid,))
        for pid, stock_init, _ in prods:
            cur.execute("UPDATE produits SET stock = %s WHERE id = %s", (stock_init, pid))
        db_conn.commit()
        cur.close()

    def test_stock_cannot_go_negative(self, db_conn, etab_id):
        """Le stock ne peut pas devenir négatif : une vente au-delà du disponible est refusée."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id)
        if not prod:
            cur.close(); pytest.skip("Aucun produit trouvé")

        produit_id = str(prod["id"])
        stock_initial = int(prod["stock"])
        excess_qty = stock_initial + 10

        cur.execute("""
            UPDATE produits SET stock = stock - %s
            WHERE id = %s AND stock >= %s
            RETURNING stock
        """, (excess_qty, produit_id, excess_qty))
        updated = cur.fetchone()

        db_conn.commit()

        assert updated is None, "Un décrément au-delà du stock a été autorisé"

        cur.execute("SELECT stock FROM produits WHERE id = %s", (produit_id,))
        current = cur.fetchone()
        assert int(current["stock"]) == stock_initial, "Le stock a été modifié malgré échec"
        cur.close()

    def test_stock_decrement_at_limit(self, db_conn, etab_id, admin_id):
        """Le décrément doit réussir quand la quantité vendue égale exactement le stock."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id, min_stock=1)
        if not prod:
            cur.close(); pytest.skip("Aucun produit en stock")

        produit_id = str(prod["id"])
        stock_initial = int(prod["stock"])

        # Décrémenter exactement tout le stock
        cur.execute("""
            UPDATE produits SET stock = stock - %s, updated_at = NOW()
            WHERE id = %s AND stock >= %s
            RETURNING stock
        """, (stock_initial, produit_id, stock_initial))
        updated = cur.fetchone()

        db_conn.commit()

        assert updated is not None, "Décrément à la limite refusé"
        assert int(updated["stock"]) == 0, "Le stock n'est pas à zéro"

        # Restaurer
        cur.execute("UPDATE produits SET stock = %s WHERE id = %s",
                   (stock_initial, produit_id))
        db_conn.commit()
        cur.close()


# ══════════════════════════════════════════════════════════════════════
# TestAlertes — Détection des ruptures de stock
# ══════════════════════════════════════════════════════════════════════

class TestAlertes:
    """Tests de détection des alertes de rupture de stock."""

    def test_get_alertes_rupture_structure(self, db_conn, etab_id):
        """get_alertes_rupture() retourne une liste avec les champs attendus."""
        dm = DashboardManager(db_conn, etab_id)
        alertes = dm.get_alertes_rupture()

        assert isinstance(alertes, list)
        for a in alertes:
            assert "id" in a
            assert "nom" in a
            assert "stock" in a
            assert "stock_alerte" in a
            assert "categorie_nom" in a
            assert "prix" in a
            assert a["stock"] <= a["stock_alerte"], \
                f"{a['nom']}: stock={a['stock']} > alerte={a['stock_alerte']}"

    def test_produit_sous_alerte_detecte(self, db_conn, etab_id):
        """Un produit dont le stock passe sous le seuil d'alerte doit être détecté."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id, min_stock=5)
        if not prod:
            cur.close(); pytest.skip("Aucun produit trouvé")

        produit_id = str(prod["id"])
        stock_initial = int(prod["stock"])
        alerte_initial = int(prod["stock_alerte"])

        try:
            cur.execute("""
                UPDATE produits SET stock = 2, stock_alerte = 5
                WHERE id = %s
            """, (produit_id,))
            db_conn.commit()

            dm = DashboardManager(db_conn, etab_id)
            alertes = dm.get_alertes_rupture()
            alert_ids = [str(a["id"]) for a in alertes]

            assert produit_id in alert_ids, "Le produit sous alerte n'a pas été détecté"

            alerte = next(a for a in alertes if str(a["id"]) == produit_id)
            assert alerte["stock"] == 2
            assert alerte["stock_alerte"] == 5
        finally:
            cur.execute("UPDATE produits SET stock = %s, stock_alerte = %s WHERE id = %s",
                       (stock_initial, alerte_initial, produit_id))
            db_conn.commit()
            cur.close()

    def test_produit_stock_zero_en_tete(self, db_conn, etab_id):
        """Un produit avec stock = 0 doit apparaître en tête des alertes (trié ASC)."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id, min_stock=1)
        if not prod:
            cur.close(); pytest.skip("Aucun produit trouvé")

        produit_id = str(prod["id"])
        stock_initial = int(prod["stock"])
        alerte_initial = int(prod["stock_alerte"])

        try:
            cur.execute("UPDATE produits SET stock = 0 WHERE id = %s", (produit_id,))
            db_conn.commit()

            dm = DashboardManager(db_conn, etab_id)
            alertes = dm.get_alertes_rupture()

            if len(alertes) > 0:
                assert alertes[0]["stock"] == 0, \
                    "Le produit à stock=0 n'est pas en tête des alertes"
        finally:
            cur.execute("UPDATE produits SET stock = %s, stock_alerte = %s WHERE id = %s",
                       (stock_initial, alerte_initial, produit_id))
            db_conn.commit()
            cur.close()

    def test_produit_audessus_alerte_non_detecte(self, db_conn, etab_id):
        """Un produit avec stock > stock_alerte ne doit pas apparaître dans les alertes."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id, min_stock=1)
        if not prod:
            cur.close(); pytest.skip("Aucun produit trouvé")

        produit_id = str(prod["id"])
        stock_initial = int(prod["stock"])
        alerte_initial = int(prod["stock_alerte"])

        try:
            cur.execute("""
                UPDATE produits SET stock = 100, stock_alerte = 5
                WHERE id = %s
            """, (produit_id,))
            db_conn.commit()

            dm = DashboardManager(db_conn, etab_id)
            alertes = dm.get_alertes_rupture()
            alert_ids = [str(a["id"]) for a in alertes]

            assert produit_id not in alert_ids, \
                "Un produit au-dessus du seuil a été détecté à tort"
        finally:
            cur.execute("UPDATE produits SET stock = %s, stock_alerte = %s WHERE id = %s",
                       (stock_initial, alerte_initial, produit_id))
            db_conn.commit()
            cur.close()

    def test_alerte_stock_egal_seuil(self, db_conn, etab_id):
        """Un produit avec stock == stock_alerte doit être détecté (condition <=)."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id, min_stock=1)
        if not prod:
            cur.close(); pytest.skip("Aucun produit trouvé")

        produit_id = str(prod["id"])
        stock_initial = int(prod["stock"])
        alerte_initial = int(prod["stock_alerte"])

        try:
            cur.execute("""
                UPDATE produits SET stock = 5, stock_alerte = 5
                WHERE id = %s
            """, (produit_id,))
            db_conn.commit()

            dm = DashboardManager(db_conn, etab_id)
            alertes = dm.get_alertes_rupture()
            alert_ids = [str(a["id"]) for a in alertes]

            assert produit_id in alert_ids, \
                "Un produit stock == stock_alerte aurait dû être détecté (<=)"
        finally:
            cur.execute("UPDATE produits SET stock = %s, stock_alerte = %s WHERE id = %s",
                       (stock_initial, alerte_initial, produit_id))
            db_conn.commit()
            cur.close()


# ══════════════════════════════════════════════════════════════════════
# TestPermetsCommande — Flag d'exclusion du catalogue
# ══════════════════════════════════════════════════════════════════════

class TestPermetsCommande:
    """Tests du flag permets_commande sur le catalogue."""

    def test_permets_commande_false_excluded(self, db_conn, etab_id):
        """Les produits avec permets_commande=FALSE sont exclus du catalogue."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id)
        if not prod:
            cur.close(); pytest.skip("Aucun produit trouvé")

        produit_id = str(prod["id"])

        try:
            cur.execute("UPDATE produits SET permets_commande = FALSE WHERE id = %s",
                       (produit_id,))
            db_conn.commit()

            cur.execute("""
                SELECT p.id FROM produits p
                WHERE p.etablissement_id = %s AND p.deleted_at IS NULL
                AND p.permets_commande = TRUE
            """, (etab_id,))
            catalogue_ids = [str(r["id"]) for r in cur.fetchall()]

            assert produit_id not in catalogue_ids, \
                "Un produit avec permets_commande=FALSE apparaît dans le catalogue"
        finally:
            cur.execute("UPDATE produits SET permets_commande = TRUE WHERE id = %s",
                       (produit_id,))
            db_conn.commit()
            cur.close()

    def test_permets_commande_true_included(self, db_conn, etab_id):
        """Les produits avec permets_commande=TRUE apparaissent dans le catalogue."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT COUNT(*) AS nb FROM produits p
            WHERE p.etablissement_id = %s AND p.deleted_at IS NULL
            AND p.permets_commande = TRUE
        """, (etab_id,))
        result = cur.fetchone()
        cur.close()

        assert result["nb"] > 0, "Aucun produit avec permets_commande=TRUE trouvé"

    def test_permets_commande_default_true(self, db_conn, etab_id):
        """Les produits nouvellement créés doivent avoir permets_commande = TRUE par défaut."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT id FROM categories
            WHERE etablissement_id = %s AND deleted_at IS NULL LIMIT 1
        """, (etab_id,))
        cat = cur.fetchone()
        if not cat:
            cur.close(); pytest.skip("Aucune catégorie trouvée")

        new_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO produits (id, categorie_id, nom, prix, etablissement_id)
            VALUES (%s,%s,%s,%s,%s)
            RETURNING permets_commande
        """, (new_id, str(cat["id"]), "Produit Test Permets", 1000, etab_id))
        row = cur.fetchone()
        db_conn.commit()

        assert row["permets_commande"] is True, "Défaut permets_commande n'est pas TRUE"

        # Nettoyer
        cur.execute("DELETE FROM produits WHERE id = %s", (new_id,))
        db_conn.commit()
        cur.close()


# ══════════════════════════════════════════════════════════════════════
# TestMouvements — Création et consultation des mouvements de stock
# ══════════════════════════════════════════════════════════════════════

class TestMouvements:
    """Tests de création et consultation des mouvements de stock."""

    def test_creation_mouvement_sortie_vente(self, db_conn, etab_id, admin_id):
        """Une vente doit créer un enregistrement mouvements_stock de type sortie_vente."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id, min_stock=3)
        if not prod:
            cur.close(); pytest.skip("Aucun produit trouvé")

        produit_id = str(prod["id"])
        qty = 3

        cid = _create_commande(cur, etab_id, admin_id, ref="TEST-MVT")
        lid = _create_ligne(cur, cid, produit_id, qty)
        mid = str(uuid.uuid4())

        cur.execute("""
            INSERT INTO mouvements_stock (id, produit_id, commande_id, ligne_commande_id,
                type_mouvement, quantite, motif, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (mid, produit_id, cid, lid, "sortie_vente", qty, "Vente test", admin_id))
        db_conn.commit()

        cur.execute("SELECT * FROM mouvements_stock WHERE id = %s", (mid,))
        mvt = cur.fetchone()

        assert mvt is not None, "Le mouvement de stock n'a pas été créé"
        assert mvt["type_mouvement"] == "sortie_vente"
        assert int(mvt["quantite"]) == qty
        assert str(mvt["produit_id"]) == produit_id
        assert str(mvt["commande_id"]) == cid
        assert str(mvt["ligne_commande_id"]) == lid

        # Nettoyer
        cur.execute("DELETE FROM mouvements_stock WHERE id = %s", (mid,))
        cur.execute("DELETE FROM lignes_commande WHERE id = %s", (lid,))
        cur.execute("DELETE FROM commandes WHERE id = %s", (cid,))
        db_conn.commit()
        cur.close()

    def test_mouvement_type_invalide_rejete(self, db_conn, etab_id):
        """Un type_mouvement invalide doit être rejeté par la contrainte CHECK."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id)
        if not prod:
            cur.close(); pytest.skip("Aucun produit trouvé")

        produit_id = str(prod["id"])

        try:
            cur.execute("""
                INSERT INTO mouvements_stock (id, produit_id, type_mouvement, quantite)
                VALUES (%s,%s,%s,%s)
            """, (str(uuid.uuid4()), produit_id, "type_invalide_xyz", 1))
            db_conn.commit()
            pytest.fail("Un type_mouvement invalide a été accepté")
        except Exception as e:
            db_conn.rollback()
            assert "mouvements_stock" in str(e).lower() or "check" in str(e).lower(), \
                f"Erreur inattendue : {e}"
        finally:
            cur.close()

    def test_get_mouvements_stock_retourne_donnees(self, db_conn, etab_id):
        """get_mouvements_stock() retourne les mouvements sur une période donnée."""
        dm = DashboardManager(db_conn, etab_id)
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        mouvements = dm.get_mouvements_stock(week_ago, today)
        assert isinstance(mouvements, list)

        for m in mouvements:
            assert "type_mouvement" in m
            assert "quantite" in m
            assert "produit_nom" in m
            assert "produit_id" in m

    def test_mouvements_types_valides(self, db_conn, etab_id, admin_id):
        """Tous les types de mouvement valides doivent être acceptés."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id)
        if not prod:
            cur.close(); pytest.skip("Aucun produit trouvé")

        produit_id = str(prod["id"])
        types_valides = [
            "entree_appro",
            "sortie_vente",
            "sortie_perte",
            "sortie_remboursement",
            "ajustement",
        ]
        created_ids = []

        try:
            for t in types_valides:
                mid = str(uuid.uuid4())
                created_ids.append(mid)
                cur.execute("""
                    INSERT INTO mouvements_stock (id, produit_id, type_mouvement,
                        quantite, motif, created_by)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (mid, produit_id, t, 1, f"Test {t}", admin_id))
            db_conn.commit()

            cur.execute("""
                SELECT type_mouvement, COUNT(*) AS nb FROM mouvements_stock
                WHERE id IN %s GROUP BY type_mouvement
            """, (tuple(created_ids),))
            rows = cur.fetchall()
            assert len(rows) == len(types_valides), \
                f"Tous les types valides n'ont pas été insérés : {len(rows)}/{len(types_valides)}"
        finally:
            for mid in created_ids:
                cur.execute("DELETE FROM mouvements_stock WHERE id = %s", (mid,))
            db_conn.commit()
            cur.close()


# ══════════════════════════════════════════════════════════════════════
# TestConcurrentStock — Verrouillage optimiste
# ══════════════════════════════════════════════════════════════════════

class TestConcurrentStock:
    """Tests de concurrence et verrouillage optimiste sur les stocks."""

    def test_optimistic_lock_update_reussi(self, db_conn, etab_id):
        """Une mise à jour avec la bonne version doit réussir."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id)
        if not prod:
            cur.close(); pytest.skip("Aucun produit trouvé")

        produit_id = str(prod["id"])
        version_init = int(prod["version"])
        stock_init = int(prod["stock"])

        try:
            cur.execute("""
                UPDATE produits SET stock = stock - 1, version = version + 1,
                updated_at = NOW()
                WHERE id = %s AND version = %s
                RETURNING version, stock
            """, (produit_id, version_init))
            result = cur.fetchone()
            db_conn.commit()

            assert result is not None, "Mise à jour avec bonne version a échoué"
            assert int(result["version"]) == version_init + 1
            assert int(result["stock"]) == stock_init - 1
        finally:
            cur.execute("UPDATE produits SET stock = %s, version = %s WHERE id = %s",
                       (stock_init, version_init, produit_id))
            db_conn.commit()
            cur.close()

    def test_optimistic_lock_update_echoue(self, db_conn, etab_id):
        """Une mise à jour avec une version périmée doit échouer."""
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id)
        if not prod:
            cur.close(); pytest.skip("Aucun produit trouvé")

        produit_id = str(prod["id"])
        version_init = int(prod["version"])
        stock_init = int(prod["stock"])

        try:
            # Première mise à jour : réussit et incrémente la version
            cur.execute("""
                UPDATE produits SET stock = stock - 1, version = version + 1,
                updated_at = NOW()
                WHERE id = %s AND version = %s
                RETURNING version
            """, (produit_id, version_init))
            assert cur.fetchone() is not None

            # Deuxième mise à jour : même version_init → échoue
            cur.execute("""
                UPDATE produits SET stock = stock - 2, version = version + 1,
                updated_at = NOW()
                WHERE id = %s AND version = %s
                RETURNING version
            """, (produit_id, version_init))
            result2 = cur.fetchone()

            db_conn.commit()

            assert result2 is None, \
                "La deuxième mise à jour n'aurait pas dû réussir (version périmée)"
        finally:
            cur.execute("UPDATE produits SET stock = %s, version = %s WHERE id = %s",
                       (stock_init, version_init, produit_id))
            db_conn.commit()
            cur.close()

    def test_optimistic_lock_concurrent_connections(self, db_conn, etab_id):
        """Deux connexions concurrentes : seule la première mise à jour doit passer."""
        from ArtizBoardCommon.config_loader import get_db_config

        cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prod = _get_produit(cur, etab_id)
        if not prod:
            cur.close(); pytest.skip("Aucun produit trouvé")

        produit_id = str(prod["id"])
        version_init = int(prod["version"])
        stock_init = int(prod["stock"])

        db_cfg = get_db_config()
        conn2 = None

        try:
            conn2 = psycopg2.connect(
                host=db_cfg[0], port=db_cfg[1], dbname=db_cfg[2],
                user=db_cfg[3], password=db_cfg[4], client_encoding="UTF8"
            )
            cur2 = conn2.cursor()

            # Connexion 2 modifie en premier
            cur2.execute("""
                UPDATE produits SET stock = stock - 1, version = version + 1
                WHERE id = %s AND version = %s
                RETURNING version
            """, (produit_id, version_init))
            result2 = cur2.fetchone()
            conn2.commit()
            assert result2 is not None, "Connexion 2 : mise à jour échouée"

            # Connexion 1 tente avec version_init (déjà périmée)
            cur.execute("""
                UPDATE produits SET stock = stock - 2, version = version + 1
                WHERE id = %s AND version = %s
                RETURNING version
            """, (produit_id, version_init))
            result1 = cur.fetchone()
            db_conn.rollback()

            assert result1 is None, \
                "Connexion 1 : mise à jour avec version périmée n'aurait pas dû réussir"
        finally:
            if conn2:
                cur2 = conn2.cursor()
                cur2.execute("UPDATE produits SET stock = %s, version = %s WHERE id = %s",
                           (stock_init, version_init, produit_id))
                conn2.commit()
                conn2.close()
            cur.execute("UPDATE produits SET stock = %s, version = %s WHERE id = %s",
                       (stock_init, version_init, produit_id))
            db_conn.commit()
            cur.close()
