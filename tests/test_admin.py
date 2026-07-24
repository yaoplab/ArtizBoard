"""Tests complets pour les opérations DB de l'application Admin (Livrable D).

Couvre : Produits CRUD, Catégories CRUD, Utilisateurs CRUD,
Activation codes, Pages établissement, Thème config, Commandes.
"""
import sys, pytest, uuid, re
sys.path.insert(0, r'C:\projet')

import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta, timezone
from apps.common.auth import AuthError


# ═══════════════════════════════════════════════════════
# Helper : réplique les méthodes DB de AdminApp sans Flet
# ═══════════════════════════════════════════════════════

class AdminDBHelper:
    """Wrapper de test qui reproduit les opérations DB de AdminApp.__main__."""

    def __init__(self, conn, auth, user: dict):
        self.conn = conn
        self.auth = auth
        self.user = user

    # ── Produits ──

    def _fetch_produits(self, search: str = "", categorie_id: str = ""):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT p.*, c.nom AS categorie_nom
            FROM produits p
            JOIN categories c ON p.categorie_id = c.id
            WHERE p.etablissement_id = %s
              AND p.deleted_at IS NULL
              AND c.deleted_at IS NULL
        """
        params = [self.user["etablissement_id"]]
        if search:
            query += " AND (p.nom ILIKE %s OR p.description ILIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        if categorie_id:
            query += " AND p.categorie_id = %s"
            params.append(categorie_id)
        query += " ORDER BY p.nom"
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def _save_produit(self, data: dict):
        cur = self.conn.cursor()
        eid = self.user["etablissement_id"]
        uid = self.user["id"]
        if data.get("id"):
            cur.execute("""
                UPDATE produits SET nom=%s, description=%s, categorie_id=%s,
                prix=%s, taux_tva=%s, stock=%s, stock_alerte=%s,
                permets_commande=%s, photo_url=%s, updated_by=%s, updated_at=NOW(),
                version = version + 1
                WHERE id=%s AND version=%s AND deleted_at IS NULL
            """, (
                data["nom"], data.get("description", ""), data["categorie_id"],
                data["prix"], data.get("taux_tva", 0), data.get("stock", 0),
                data.get("stock_alerte", 5), data.get("permets_commande", True),
                data.get("photo_url", ""),
                uid, data["id"], data.get("version", 1),
            ))
            if cur.rowcount == 0:
                self.conn.rollback()
                cur.close()
                raise ValueError("Produit modifié par un autre utilisateur. Rechargez.")
        else:
            pid = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO produits (id, categorie_id, nom, description, photo_url, prix,
                taux_tva, stock, stock_alerte, permets_commande,
                etablissement_id, created_by, updated_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                pid, data["categorie_id"], data["nom"],
                data.get("description", ""), data.get("photo_url", ""), data["prix"],
                data.get("taux_tva", 0), data.get("stock", 0),
                data.get("stock_alerte", 5), data.get("permets_commande", True),
                eid, uid, uid,
            ))
        self.conn.commit()
        cur.close()

    def _delete_produit(self, produit_id: str):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE produits SET deleted_at=NOW(), updated_by=%s "
            "WHERE id=%s AND deleted_at IS NULL",
            (self.user["id"], produit_id),
        )
        self.conn.commit()
        cur.close()

    # ── Catégories ──

    def _fetch_categories(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM categories WHERE etablissement_id = %s "
            "AND deleted_at IS NULL ORDER BY nom",
            (self.user["etablissement_id"],),
        )
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def _save_categorie(self, data: dict):
        cur = self.conn.cursor()
        cid = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO categories (id, nom, icone, etablissement_id, created_by, updated_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (cid, data["nom"], data.get("icone", "category"),
              self.user["etablissement_id"], self.user["id"], self.user["id"]))
        self.conn.commit()
        cur.close()
        return cid

    # ── Utilisateurs ──

    def _fetch_users(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT u.*, r.nom AS role_nom
            FROM utilisateurs u
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.etablissement_id = %s AND u.deleted_at IS NULL
            ORDER BY u.created_at DESC
        """, (self.user["etablissement_id"],))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def _save_user(self, data: dict):
        cur = self.conn.cursor()
        if data.get("id"):
            sets = "nom=%s, email=%s, role_id=%s, updated_by=%s, updated_at=NOW(), version=version+1"
            vals = [data["nom"], data["email"], data["role_id"],
                    self.user["id"], data["id"], data.get("version", 1)]
            if data.get("password"):
                sets += ", password_hash=%s"
                vals.insert(-2, self.auth.hash_password(data["password"]))
            cur.execute(
                f"UPDATE utilisateurs SET {sets} WHERE id=%s "
                f"AND version=%s AND deleted_at IS NULL", vals
            )
            if cur.rowcount == 0:
                self.conn.rollback()
                cur.close()
                raise ValueError("Utilisateur modifié par un autre.")
        else:
            uid = str(uuid.uuid4())
            pw = self.auth.hash_password(data["password"])
            cur.execute("""
                INSERT INTO utilisateurs (id, etablissement_id, nom, email, role_id,
                    password_hash, created_by, updated_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (uid, self.user["etablissement_id"], data["nom"], data["email"],
                  data["role_id"], pw, self.user["id"], self.user["id"]))
        self.conn.commit()
        cur.close()

    # ── Activation ──

    def _gen_activation(self, utilisateur_id: str = None):
        return self.auth.generate_activation(self.user["id"], utilisateur_id)

    # ── Pages établissement ──

    def _fetch_pages(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT * FROM pages_etablissement
            WHERE etablissement_id=%s AND deleted_at IS NULL
            ORDER BY ordre, numero_page
        """, (self.user["etablissement_id"],))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def _save_page(self, data: dict):
        cur = self.conn.cursor()
        eid = self.user["etablissement_id"]
        uid = self.user["id"]
        if data.get("id"):
            cur.execute("""
                UPDATE pages_etablissement SET numero_page=%s, titre=%s,
                    contenu_html=%s, contenu_css=%s, est_active=%s,
                    ordre=%s, updated_by=%s, updated_at=NOW(), version=version+1
                WHERE id=%s AND version=%s AND deleted_at IS NULL
            """, (
                data["numero_page"], data["titre"], data.get("contenu_html", ""),
                data.get("contenu_css", ""), data.get("est_active", True),
                data.get("ordre", 0), uid, data["id"], data.get("version", 1),
            ))
            if cur.rowcount == 0:
                self.conn.rollback()
                cur.close()
                raise ValueError("Page modifiée par un autre utilisateur. Rechargez.")
        else:
            pid = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO pages_etablissement (id, etablissement_id, numero_page,
                    titre, contenu_html, contenu_css, est_active, ordre,
                    created_by, updated_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                pid, eid, data["numero_page"], data["titre"],
                data.get("contenu_html", ""), data.get("contenu_css", ""),
                data.get("est_active", True), data.get("ordre", 0), uid, uid,
            ))
        self.conn.commit()
        cur.close()

    def _delete_page(self, page_id: str):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE pages_etablissement SET deleted_at=NOW(), updated_by=%s "
            "WHERE id=%s AND deleted_at IS NULL",
            (self.user["id"], page_id),
        )
        self.conn.commit()
        cur.close()

    # ── Thème ──

    def _fetch_theme_config(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT * FROM theme_config
            WHERE etablissement_id=%s AND deleted_at IS NULL
            ORDER BY created_at LIMIT 1
        """, (self.user["etablissement_id"],))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else {}

    def _fetch_theme_presets(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT theme_id, theme_name, primary_color, secondary_color, accent_color,
                   surface_color, font_heading, hero_title, hero_subtitle, custom_css
            FROM theme_config
            WHERE deleted_at IS NULL AND est_actif = TRUE
            ORDER BY theme_id
        """)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def _save_theme_config(self, data: dict):
        cur = self.conn.cursor()
        eid = self.user["etablissement_id"]
        uid = self.user["id"]
        tc = self._fetch_theme_config()
        if tc.get("id"):
            cur.execute("""
                UPDATE theme_config SET
                    theme_id=%s, primary_color=%s, secondary_color=%s, accent_color=%s,
                    surface_color=%s, font_heading=%s, hero_title=%s,
                    hero_subtitle=%s, hero_button_text=%s, hero_image_url=%s,
                    footer_text=%s, seo_title_template=%s, seo_description=%s,
                    facebook_url=%s, instagram_url=%s, whatsapp_number=%s,
                    custom_css=%s, updated_by=%s, updated_at=NOW(), version=version+1
                WHERE id=%s AND version=%s AND deleted_at IS NULL
            """, (
                data.get("theme_id"), data.get("primary_color"), data.get("secondary_color"),
                data.get("accent_color"), data.get("surface_color"), data.get("font_heading"),
                data.get("hero_title"), data.get("hero_subtitle"), data.get("hero_button_text"),
                data.get("hero_image_url"), data.get("footer_text"),
                data.get("seo_title_template"), data.get("seo_description"),
                data.get("facebook_url"), data.get("instagram_url"), data.get("whatsapp_number"),
                data.get("custom_css"), uid, tc["id"], tc.get("version", 1),
            ))
            if cur.rowcount == 0:
                self.conn.rollback()
                cur.close()
                raise ValueError("Modifié par un autre utilisateur.")
        else:
            cid = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO theme_config (id, etablissement_id, theme_id, primary_color,
                    secondary_color, accent_color, surface_color, font_heading,
                    hero_title, hero_subtitle, hero_button_text, hero_image_url,
                    footer_text, seo_title_template, seo_description,
                    facebook_url, instagram_url, whatsapp_number,
                    custom_css, created_by, updated_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                cid, eid, data.get("theme_id"), data.get("primary_color"),
                data.get("secondary_color"), data.get("accent_color"),
                data.get("surface_color"), data.get("font_heading"),
                data.get("hero_title"), data.get("hero_subtitle"),
                data.get("hero_button_text"), data.get("hero_image_url"),
                data.get("footer_text"), data.get("seo_title_template"),
                data.get("seo_description"), data.get("facebook_url"),
                data.get("instagram_url"), data.get("whatsapp_number"),
                data.get("custom_css"), uid, uid,
            ))
        self.conn.commit()
        cur.close()

    # ── Commandes ──

    def _fetch_commandes(self, statut: str = ""):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT c.*, u.nom AS client_nom, s.nom AS staff_nom
            FROM commandes c
            LEFT JOIN utilisateurs u ON c.client_id = u.id AND u.deleted_at IS NULL
            LEFT JOIN utilisateurs s ON c.staff_id = s.id AND s.deleted_at IS NULL
            WHERE c.etablissement_id = %s AND c.deleted_at IS NULL
        """
        params = [self.user["etablissement_id"]]
        if statut:
            query += " AND c.statut = %s"
            params.append(statut)
        query += " ORDER BY c.created_at DESC LIMIT 50"
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def _fetch_lignes(self, commande_id: str):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT lc.*, p.nom AS produit_nom
            FROM lignes_commande lc
            JOIN produits p ON lc.produit_id = p.id
            WHERE lc.commande_id = %s AND lc.deleted_at IS NULL
        """, (commande_id,))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def _change_statut(self, commande_id: str, new_statut: str):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE commandes SET statut = %s, updated_by = %s, updated_at = NOW()
            WHERE id = %s AND deleted_at IS NULL
        """, (new_statut, self.user["id"], commande_id))
        self.conn.commit()
        cur.close()

    # ── Helper : récupérer un role_id par nom ──

    def _get_role_id(self, role_nom: str) -> str:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM roles WHERE nom = %s", (role_nom,))
        r = cur.fetchone()
        cur.close()
        return str(r[0]) if r else None


# ═══════════════════════════════════════════════════════
# Fixture : helper configuré
# ═══════════════════════════════════════════════════════

@pytest.fixture
def hlp(db_conn, auth, admin_id, etab_id):
    """Retourne un AdminDBHelper connecté avec l'admin seed."""
    if not admin_id or not etab_id:
        pytest.skip("Seed data manquant (admin/etablissement)")
    user = {
        "id": admin_id,
        "email": "admin@larepublique.tg",
        "nom": "Admin Test",
        "role": "admin",
        "etablissement_id": etab_id,
        "etablissement_nom": "Établissement Test",
    }
    return AdminDBHelper(db_conn, auth, user)


# ═══════════════════════════════════════════════════════
# Helpers pour créer / nettoyer les données de test
# ═══════════════════════════════════════════════════════

TAG = "_TSTADM_"  # préfixe pour identifier les données de test


def _make_test_cat(hlp, suffix: str = "") -> str:
    """Crée une catégorie de test et retourne son id. Nettoie au plus tôt."""
    cid = hlp._save_categorie({"nom": TAG + "Cat" + suffix, "icone": "test"})
    return cid


def _cleanup_cat(hlp, cat_id: str):
    try:
        hlp.conn.rollback()
    except Exception:
        pass
    hlp.conn.cursor().execute(
        "UPDATE categories SET deleted_at=NOW() WHERE id=%s", (cat_id,))
    hlp.conn.commit()


def _cleanup_prod(hlp, prod_id: str):
    try:
        hlp.conn.rollback()
    except Exception:
        pass
    hlp.conn.cursor().execute(
        "DELETE FROM lignes_commande WHERE produit_id=%s", (prod_id,))
    hlp.conn.cursor().execute(
        "DELETE FROM produits WHERE id=%s", (prod_id,))
    hlp.conn.commit()


def _make_test_prod(hlp, cat_id: str, suffix: str = "", **overrides) -> dict:
    """Crée un produit de test via _save_produit, retourne ses données DB."""
    data = {
        "categorie_id": cat_id,
        "nom": TAG + "Produit" + suffix,
        "description": "Description test" + suffix,
        "prix": 1500,
        "taux_tva": 18,
        "stock": 25,
        "stock_alerte": 5,
        "permets_commande": True,
        "photo_url": "https://example.com/photo" + suffix + ".jpg",
    }
    data.update(overrides)
    hlp._save_produit(data)
    prods = hlp._fetch_produits(categorie_id=cat_id)
    return next((p for p in prods if p["nom"] == data["nom"]), None)


def _cleanup_user(hlp, user_id: str):
    try:
        hlp.conn.rollback()
    except Exception:
        pass
    cur = hlp.conn.cursor()
    cur.execute("DELETE FROM activation_codes WHERE utilisateur_id=%s", (user_id,))
    cur.execute("DELETE FROM devices WHERE utilisateur_id=%s", (user_id,))
    cur.execute("DELETE FROM utilisateurs WHERE id=%s", (user_id,))
    hlp.conn.commit()


def _cleanup_page(hlp, page_id: str):
    try:
        hlp.conn.rollback()
    except Exception:
        pass
    hlp.conn.cursor().execute(
        "DELETE FROM pages_etablissement WHERE id=%s", (page_id,))
    hlp.conn.commit()


def _cleanup_theme(hlp, theme_id: str = None):
    try:
        hlp.conn.rollback()
    except Exception:
        pass
    cur = hlp.conn.cursor()
    if theme_id:
        cur.execute("DELETE FROM theme_config WHERE id=%s", (theme_id,))
    else:
        cur.execute("DELETE FROM theme_config WHERE etablissement_id=%s",
                    (hlp.user["etablissement_id"],))
    hlp.conn.commit()


def _consolidate_theme(hlp):
    """Garantit qu'un seul theme_config existe pour l'etablissement.
    Supprime les doublons et conserve le plus recent (par created_at DESC)."""
    eid = hlp.user["etablissement_id"]
    try:
        hlp.conn.rollback()
    except Exception:
        pass
    cur = hlp.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, created_at FROM theme_config
        WHERE etablissement_id=%s AND deleted_at IS NULL
        ORDER BY created_at DESC
    """, (eid,))
    rows = cur.fetchall()
    cur.close()
    if len(rows) > 1:
        keep_id = rows[0]["id"]
        cur = hlp.conn.cursor()
        for r in rows[1:]:
            cur.execute("DELETE FROM theme_config WHERE id=%s", (r["id"],))
        hlp.conn.commit()
        cur.close()


# ═══════════════════════════════════════════════════════
# Tests : Produits CRUD
# ═══════════════════════════════════════════════════════

class TestProduits:
    """Tests CRUD sur les produits : création, lecture, mise à jour,
    suppression (soft delete), verrouillage optimiste et URL photo."""

    def test_create_produit(self, hlp):
        """Crée un produit et vérifie qu'il apparaît dans fetch_produits."""
        cat_id = _make_test_cat(hlp, "_create")
        try:
            prod = _make_test_prod(hlp, cat_id, "_create")
            assert prod is not None
            assert TAG in prod["nom"]
            assert float(prod["prix"]) == 1500
            assert prod["photo_url"] == "https://example.com/photo_create.jpg"
        finally:
            _cleanup_cat(hlp, cat_id)
            if prod:
                _cleanup_prod(hlp, prod["id"])

    def test_read_produits_empty_category(self, hlp):
        """Vérifie que fetch_produits retourne une liste vide pour une
        catégorie sans produits."""
        cat_id = _make_test_cat(hlp, "_empty")
        try:
            prods = hlp._fetch_produits(categorie_id=cat_id)
            assert prods == []
        finally:
            _cleanup_cat(hlp, cat_id)

    def test_read_produits_with_search(self, hlp):
        """Vérifie que le filtre de recherche texte fonctionne."""
        cat_id = _make_test_cat(hlp, "_srch")
        try:
            _make_test_prod(hlp, cat_id, "_RECH")
            _make_test_prod(hlp, cat_id, "_AUTRE")
            results = hlp._fetch_produits(search="RECH")
            assert len(results) == 1
            assert "RECH" in results[0]["nom"]
        finally:
            _cleanup_cat(hlp, cat_id)
            cur = hlp.conn.cursor()
            cur.execute("DELETE FROM produits WHERE nom LIKE %s", (TAG + "%",))
            hlp.conn.commit()

    def test_read_produits_with_categorie_filter(self, hlp):
        """Vérifie le filtrage par catégorie sur fetch_produits."""
        cat_a = _make_test_cat(hlp, "_filtA")
        cat_b = _make_test_cat(hlp, "_filtB")
        try:
            _make_test_prod(hlp, cat_a, "_A")
            _make_test_prod(hlp, cat_b, "_B")
            prods_a = hlp._fetch_produits(categorie_id=cat_a)
            prods_b = hlp._fetch_produits(categorie_id=cat_b)
            assert len(prods_a) == 1
            assert len(prods_b) == 1
        finally:
            _cleanup_cat(hlp, cat_a)
            _cleanup_cat(hlp, cat_b)
            cur = hlp.conn.cursor()
            cur.execute("DELETE FROM produits WHERE nom LIKE %s", (TAG + "%",))
            hlp.conn.commit()

    def test_update_produit(self, hlp):
        """Met à jour le nom, le prix et le stock d'un produit existant."""
        cat_id = _make_test_cat(hlp, "_upd")
        try:
            prod = _make_test_prod(hlp, cat_id, "_upd")
            version_before = prod["version"]
            hlp._save_produit({
                "id": prod["id"],
                "nom": TAG + "Modifié",
                "description": "Desc modifiée",
                "categorie_id": cat_id,
                "prix": 2990,
                "taux_tva": 10,
                "stock": 50,
                "stock_alerte": 10,
                "permets_commande": False,
                "photo_url": "https://example.com/updated.jpg",
                "version": version_before,
            })
            updated_prods = hlp._fetch_produits(categorie_id=cat_id)
            updated = next((p for p in updated_prods if p["id"] == prod["id"]), None)
            assert updated is not None
            assert updated["nom"] == TAG + "Modifié"
            assert float(updated["prix"]) == 2990
            assert updated["stock"] == 50
            assert updated["version"] == version_before + 1
        finally:
            _cleanup_cat(hlp, cat_id)
            _cleanup_prod(hlp, prod["id"])

    def test_delete_produit_soft(self, hlp):
        """Soft-delete un produit et vérifie qu'il n'apparaît plus."""
        cat_id = _make_test_cat(hlp, "_del")
        try:
            prod = _make_test_prod(hlp, cat_id, "_del")
            hlp._delete_produit(prod["id"])
            prods = hlp._fetch_produits(categorie_id=cat_id)
            assert not any(p["id"] == prod["id"] for p in prods)
            # Vérifie que l'enregistrement existe encore (soft delete)
            cur = hlp.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM produits WHERE id=%s", (prod["id"],))
            row = cur.fetchone()
            cur.close()
            assert row is not None
            assert row["deleted_at"] is not None
        finally:
            _cleanup_cat(hlp, cat_id)
            _cleanup_prod(hlp, prod["id"])

    def test_update_produit_optimistic_lock_fails(self, hlp):
        """Vérifie que le verrouillage optimiste bloque une mise à jour
        avec une version périmée (conflit de concurrence simulé)."""
        cat_id = _make_test_cat(hlp, "_lock")
        try:
            prod = _make_test_prod(hlp, cat_id, "_lock")
            # Première modification : utilise la version correcte -> succès
            hlp._save_produit({
                "id": prod["id"], "nom": TAG + "Mod1", "description": "",
                "categorie_id": cat_id, "prix": 1000, "taux_tva": 0,
                "stock": 10, "stock_alerte": 5, "permets_commande": True,
                "photo_url": "", "version": prod["version"],
            })
            # Deuxième modification avec version périmée -> échec
            with pytest.raises(ValueError, match="modifié par un autre"):
                hlp._save_produit({
                    "id": prod["id"], "nom": TAG + "Mod2", "description": "",
                    "categorie_id": cat_id, "prix": 2000, "taux_tva": 0,
                    "stock": 20, "stock_alerte": 5, "permets_commande": True,
                    "photo_url": "", "version": prod["version"],
                })
        finally:
            _cleanup_cat(hlp, cat_id)
            _cleanup_prod(hlp, prod["id"])

    def test_photo_url_persisted(self, hlp):
        """Vérifie qu'une URL de photo est correctement sauvegardée et relue."""
        cat_id = _make_test_cat(hlp, "_photo")
        try:
            photo = "https://supabase.co/storage/v1/object/public/images/abc123_photo.jpg"
            prod = _make_test_prod(hlp, cat_id, "_photo", photo_url=photo)
            assert prod["photo_url"] == photo
        finally:
            _cleanup_cat(hlp, cat_id)
            if prod:
                _cleanup_prod(hlp, prod["id"])

    def test_create_produit_without_name_fails(self, hlp):
        """Vérifie qu'un produit sans nom lève une erreur (contrainte NOT NULL)."""
        cat_id = _make_test_cat(hlp, "_noname")
        try:
            with pytest.raises(Exception):
                hlp._save_produit({
                    "categorie_id": cat_id,
                    "nom": None,
                    "prix": 1000,
                })
        finally:
            _cleanup_cat(hlp, cat_id)


# ═══════════════════════════════════════════════════════
# Tests : Catégories CRUD
# ═══════════════════════════════════════════════════════

class TestCategories:
    """Tests CRUD sur les catégories : création et lecture."""

    def test_create_categorie(self, hlp):
        """Crée une catégorie et vérifie qu'elle est présente dans la liste."""
        cid = hlp._save_categorie({"nom": TAG + "Boissons", "icone": "local_drink"})
        cats = hlp._fetch_categories()
        created = next((c for c in cats if c["id"] == cid), None)
        assert created is not None
        assert created["nom"] == TAG + "Boissons"
        _cleanup_cat(hlp, cid)

    def test_fetch_categories_returns_list(self, hlp):
        """Vérifie que _fetch_categories retourne bien une liste."""
        cats = hlp._fetch_categories()
        assert isinstance(cats, list)
        # Vérifie qu'au moins la catégorie créée existe
        cid = _make_test_cat(hlp, "_list")
        cats2 = hlp._fetch_categories()
        assert len(cats2) >= 1
        _cleanup_cat(hlp, cid)

    def test_create_categorie_persists_data(self, hlp):
        """Vérifie que la catégorie créée est bien persistée avec son icône."""
        cid = hlp._save_categorie({"nom": TAG + "TestIcon", "icone": "star"})
        cats = hlp._fetch_categories()
        created = next((c for c in cats if c["id"] == cid), None)
        assert created is not None
        assert created["nom"] == TAG + "TestIcon"
        assert created["icone"] == "star"
        _cleanup_cat(hlp, cid)


# ═══════════════════════════════════════════════════════
# Tests : Utilisateurs CRUD
# ═══════════════════════════════════════════════════════

class TestUsers:
    """Tests CRUD sur les utilisateurs : lecture, création et mise à jour."""

    def test_fetch_users_returns_list(self, hlp):
        """Vérifie que fetch_users retourne une liste contenant l'admin."""
        users = hlp._fetch_users()
        assert isinstance(users, list)
        assert len(users) >= 1
        admin = next((u for u in users if u["id"] == hlp.user["id"]), None)
        assert admin is not None
        assert admin["email"] == "admin@larepublique.tg"

    def test_create_user(self, hlp):
        """Crée un utilisateur serveur et vérifie qu'il apparaît dans la liste."""
        role_id = hlp._get_role_id("serveur")
        if not role_id:
            pytest.skip("Rôle 'serveur' introuvable")
        hlp._save_user({
            "nom": TAG + "Serveur",
            "email": TAG.lower() + "serveur@test.tg",
            "role_id": role_id,
            "password": "password123",
        })
        users = hlp._fetch_users()
        created = next((u for u in users if u["email"] == TAG.lower() + "serveur@test.tg"), None)
        assert created is not None
        assert created["nom"] == TAG + "Serveur"
        _cleanup_user(hlp, created["id"])

    def test_update_user_email(self, hlp):
        """Modifie l'email et le nom d'un utilisateur existant."""
        role_id = hlp._get_role_id("serveur")
        if not role_id:
            pytest.skip("Rôle 'serveur' introuvable")
        # Créer un utilisateur test
        hlp._save_user({
            "nom": TAG + "AVANT",
            "email": TAG.lower() + "avant@test.tg",
            "role_id": role_id,
            "password": "password123",
        })
        users = hlp._fetch_users()
        u = next((x for x in users if x["email"] == TAG.lower() + "avant@test.tg"), None)
        assert u is not None
        # Mise à jour
        hlp._save_user({
            "id": u["id"],
            "nom": TAG + "APRES",
            "email": TAG.lower() + "apres@test.tg",
            "role_id": role_id,
            "version": u["version"],
        })
        users2 = hlp._fetch_users()
        updated = next((x for x in users2 if x["id"] == u["id"]), None)
        assert updated is not None
        assert updated["nom"] == TAG + "APRES"
        assert updated["email"] == TAG.lower() + "apres@test.tg"
        _cleanup_user(hlp, u["id"])

    def test_create_user_missing_password_fails(self, hlp):
        """Vérifie qu'on ne peut pas créer un utilisateur sans mot de passe."""
        role_id = hlp._get_role_id("serveur")
        if not role_id:
            pytest.skip("Rôle 'serveur' introuvable")
        with pytest.raises(Exception):
            hlp._save_user({
                "nom": TAG + "NoPass",
                "email": TAG.lower() + "nopass@test.tg",
                "role_id": role_id,
            })


# ═══════════════════════════════════════════════════════
# Tests : Codes d'activation
# ═══════════════════════════════════════════════════════

class TestActivation:
    """Tests des codes d'activation : génération et validation."""

    def test_generate_activation_format(self, hlp):
        """Vérifie que le code généré fait 8 caractères hexadécimaux
        et que l'URL contient 'http'."""
        code, url = hlp._gen_activation(hlp.user["id"])
        assert len(code) == 8
        assert re.match(r'^[0-9a-f]{8}$', code)
        assert "http" in url

    def test_activate_device_valid_code(self, hlp):
        """Valide un code d'activation fraîchement généré et obtient un token."""
        code, _ = hlp._gen_activation(hlp.user["id"])
        access, refresh, info = hlp.auth.activate_device(
            code, "TestDevice_Admin", "192.168.1.100"
        )
        assert isinstance(access, str)
        assert len(access) > 20
        assert isinstance(refresh, str)
        assert info["id"] == hlp.user["id"]

    def test_activate_device_invalid_code(self, hlp):
        """Vérifie qu'un code invalide lève AuthError."""
        with pytest.raises(AuthError, match="invalide"):
            hlp.auth.activate_device("ffffffff", "BadDevice", "127.0.0.1")

    def test_activate_device_empty_token(self, hlp):
        """Vérifie qu'un token vide lève AuthError."""
        with pytest.raises(AuthError):
            hlp.auth.activate_device("", "EmptyDevice", "127.0.0.1")


# ═══════════════════════════════════════════════════════
# Tests : Pages établissement
# ═══════════════════════════════════════════════════════

class TestPages:
    """Tests CRUD sur les pages d'établissement : création, lecture,
    mise à jour, suppression (soft delete) et verrouillage optimiste."""

    def test_create_page(self, hlp):
        """Crée une page établissement et vérifie son apparition."""
        hlp._save_page({
            "numero_page": 1,
            "titre": TAG + "Notre Histoire",
            "contenu_html": "<h2>Histoire</h2><p>Texte</p>",
            "contenu_css": ".histoire { color: blue; }",
            "est_active": True,
            "ordre": 1,
        })
        pages = hlp._fetch_pages()
        page = next((p for p in pages if p["titre"] == TAG + "Notre Histoire"), None)
        assert page is not None
        assert page["numero_page"] == 1
        assert page["est_active"] is True
        _cleanup_page(hlp, page["id"])

    def test_fetch_pages_empty(self, hlp):
        """Vérifie que fetch_pages retourne une liste vide si aucune page test."""
        pages = hlp._fetch_pages()
        # Seulement les pages de test (si cleanup avant) + pages seed
        assert isinstance(pages, list)
        test_pages = [p for p in pages if TAG in p.get("titre", "")]
        assert test_pages == []

    def test_update_page(self, hlp):
        """Met à jour le titre et le contenu d'une page existante."""
        hlp._save_page({
            "numero_page": 5, "titre": TAG + "Avant",
            "contenu_html": "<p>old</p>", "contenu_css": "",
            "est_active": True, "ordre": 5,
        })
        pages = hlp._fetch_pages()
        page = next((p for p in pages if p["titre"] == TAG + "Avant"), None)
        assert page is not None
        hlp._save_page({
            "id": page["id"], "numero_page": 5, "titre": TAG + "Apres",
            "contenu_html": "<p>new</p>", "contenu_css": ".new{}",
            "est_active": False, "ordre": 5, "version": page["version"],
        })
        pages2 = hlp._fetch_pages()
        updated = next((p for p in pages2 if p["id"] == page["id"]), None)
        assert updated is not None
        assert updated["titre"] == TAG + "Apres"
        assert updated["est_active"] is False
        _cleanup_page(hlp, page["id"])

    def test_delete_page_soft(self, hlp):
        """Soft-delete une page et vérifie qu'elle disparaît du fetch."""
        hlp._save_page({
            "numero_page": 99, "titre": TAG + "À supprimer",
            "contenu_html": "<p>x</p>", "contenu_css": "",
            "est_active": True, "ordre": 99,
        })
        pages = hlp._fetch_pages()
        page = next((p for p in pages if p["titre"] == TAG + "À supprimer"), None)
        assert page is not None
        hlp._delete_page(page["id"])
        pages2 = hlp._fetch_pages()
        assert not any(p["id"] == page["id"] for p in pages2)
        _cleanup_page(hlp, page["id"])

    def test_optimistic_lock_page_fails(self, hlp):
        """Vérifie que deux mises à jour concurrentes sur une page sont bloquées."""
        hlp._save_page({
            "numero_page": 10, "titre": TAG + "LockPage",
            "contenu_html": "<p>v1</p>", "contenu_css": "",
            "est_active": True, "ordre": 10,
        })
        pages = hlp._fetch_pages()
        page = next((p for p in pages if p["titre"] == TAG + "LockPage"), None)
        # Première modif ok
        hlp._save_page({
            "id": page["id"], "numero_page": 10, "titre": TAG + "LockPage",
            "contenu_html": "<p>v2</p>", "contenu_css": "",
            "est_active": True, "ordre": 10, "version": page["version"],
        })
        # Deuxième modif avec version périmée
        with pytest.raises(ValueError, match="modifiée par un autre"):
            hlp._save_page({
                "id": page["id"], "numero_page": 10, "titre": TAG + "LockPage",
                "contenu_html": "<p>v3</p>", "contenu_css": "",
                "est_active": True, "ordre": 10, "version": page["version"],
            })
        _cleanup_page(hlp, page["id"])


# ═══════════════════════════════════════════════════════
# Tests : Configuration du thème
# ═══════════════════════════════════════════════════════

class TestTheme:
    """Tests de la configuration du thème : lecture, création, mise à jour,
    presets et verrouillage optimiste."""

    def test_fetch_theme_config_returns_dict(self, hlp):
        """Vérifie que fetch_theme_config retourne bien un dict
        (vide ou peuplé selon les données existantes)."""
        _consolidate_theme(hlp)
        tc = hlp._fetch_theme_config()
        assert isinstance(tc, dict)
        if tc:
            assert "theme_id" in tc or tc == {}
        else:
            assert tc == {}

    def test_create_theme_config(self, hlp):
        """Crée ou met à jour une configuration de thème et vérifie sa lecture."""
        _consolidate_theme(hlp)
        hlp._save_theme_config({
            "theme_id": "artizboard",
            "primary_color": "#FF0000",
            "secondary_color": "#00FF00",
            "accent_color": "#0000FF",
            "surface_color": "#FFFFFF",
            "font_heading": "Roboto",
            "hero_title": TAG + "Bienvenue",
            "hero_subtitle": "Sous-titre test",
            "hero_button_text": "Découvrir",
            "hero_image_url": "https://img.example.com/hero.jpg",
            "footer_text": "© Test",
            "seo_title_template": "{page} — Test",
            "seo_description": "Desc SEO test",
            "facebook_url": "https://fb.com/test",
            "instagram_url": "https://insta.com/test",
            "whatsapp_number": "+22890000000",
            "custom_css": "body { background: red; }",
        })
        tc = hlp._fetch_theme_config()
        assert tc != {}
        assert tc["primary_color"] == "#FF0000"
        assert tc["hero_title"] == TAG + "Bienvenue"
        assert tc["whatsapp_number"] == "+22890000000"

    def test_update_theme_config(self, hlp):
        """Met à jour une configuration de thème existante puis restaure."""
        _consolidate_theme(hlp)
        orig = hlp._fetch_theme_config()
        if not orig:
            hlp._save_theme_config({
                "theme_id": "artizboard", "primary_color": "#AAA",
                "secondary_color": "#BBB", "accent_color": "#CCC",
                "surface_color": "#DDD", "font_heading": "Inter",
                "hero_title": "T0", "hero_subtitle": "S0",
                "hero_button_text": "B0", "hero_image_url": "",
                "footer_text": "", "seo_title_template": "",
                "seo_description": "", "facebook_url": "",
                "instagram_url": "", "whatsapp_number": "",
                "custom_css": "",
            })
            orig = hlp._fetch_theme_config()
        # Sauvegarder valeurs originales pour restauration
        orig_theme = orig.get("theme_id")
        orig_primary = orig.get("primary_color")
        hlp._save_theme_config({
            "theme_id": "light_mode", "primary_color": "#EEE",
            "secondary_color": "#DDD", "accent_color": "#CCC",
            "surface_color": "#FFF", "font_heading": "Open Sans",
            "hero_title": "T2", "hero_subtitle": "ST2",
            "hero_button_text": "Start", "hero_image_url": "",
            "footer_text": "", "seo_title_template": "",
            "seo_description": "", "facebook_url": "",
            "instagram_url": "", "whatsapp_number": "",
            "custom_css": "",
        })
        tc2 = hlp._fetch_theme_config()
        assert tc2["primary_color"] == "#EEE"
        # Restaurer
        hlp._save_theme_config({
            "theme_id": orig_theme, "primary_color": orig_primary,
            "secondary_color": orig.get("secondary_color", ""),
            "accent_color": orig.get("accent_color", ""),
            "surface_color": orig.get("surface_color", ""),
            "font_heading": orig.get("font_heading", ""),
            "hero_title": orig.get("hero_title", ""),
            "hero_subtitle": orig.get("hero_subtitle", ""),
            "hero_button_text": orig.get("hero_button_text", ""),
            "hero_image_url": orig.get("hero_image_url", ""),
            "footer_text": orig.get("footer_text", ""),
            "seo_title_template": orig.get("seo_title_template", ""),
            "seo_description": orig.get("seo_description", ""),
            "facebook_url": orig.get("facebook_url", ""),
            "instagram_url": orig.get("instagram_url", ""),
            "whatsapp_number": orig.get("whatsapp_number", ""),
            "custom_css": orig.get("custom_css", ""),
        })

    def test_fetch_theme_presets(self, hlp):
        """Vérifie que fetch_theme_presets retourne une liste."""
        presets = hlp._fetch_theme_presets()
        assert isinstance(presets, list)
        for p in presets:
            assert "theme_id" in p
            assert "theme_name" in p
            assert "primary_color" in p

    def test_optimistic_lock_theme_fails(self, hlp):
        """Vérifie le verrouillage optimiste sur theme_config."""
        _consolidate_theme(hlp)
        orig = hlp._fetch_theme_config()
        if not orig:
            hlp._save_theme_config({
                "theme_id": "lock_test", "primary_color": "#AAA",
                "secondary_color": "#BBB", "accent_color": "#CCC",
                "surface_color": "#DDD", "font_heading": "Sans",
                "hero_title": "H1", "hero_subtitle": "S1",
                "hero_button_text": "B1", "hero_image_url": "",
                "footer_text": "", "seo_title_template": "",
                "seo_description": "", "facebook_url": "",
                "instagram_url": "", "whatsapp_number": "",
                "custom_css": "",
            })
            orig = hlp._fetch_theme_config()
        version_first = orig["version"]
        # Première modif ok (utilise version_first)
        hlp._save_theme_config({
            "theme_id": "lock_test", "primary_color": "#AAA2",
            "secondary_color": "#BBB", "accent_color": "#CCC",
            "surface_color": "#DDD", "font_heading": "Sans",
            "hero_title": "H1", "hero_subtitle": "S1",
            "hero_button_text": "B1", "hero_image_url": "",
            "footer_text": "", "seo_title_template": "",
            "seo_description": "", "facebook_url": "",
            "instagram_url": "", "whatsapp_number": "",
            "custom_css": "",
        })
        # Le _save_theme_config lit tc = _fetch_theme_config() en interne,
        # puis utilise tc["version"]. Donc apres la 1ere modif, version a changé.
        # Pour la 2e tentative: sauvegarder manuellement avec l'ancienne version
        # en contournant le auto-fetch du _save_theme_config
        tc_bad = orig.copy()
        tc_bad["theme_id"] = "lock_test"
        tc_bad["primary_color"] = "#BAD"
        with pytest.raises(ValueError, match="autre utilisateur"):
            # On appelle _save_theme_config mais le rowcount sera 0
            # car version est dépassée après la 1ère modif
            # ATTENTION: _save_theme_config refetch tc en interne avec la
            # version actuelle. On doit utiliser le rollback trick.
            cur = hlp.conn.cursor()
            cur.execute("""
                UPDATE theme_config SET
                    primary_color=%s, updated_by=%s, updated_at=NOW(), version=version+1
                WHERE id=%s AND version=%s AND deleted_at IS NULL
            """, ("#BAD", hlp.user["id"], orig["id"], version_first))
            if cur.rowcount == 0:
                hlp.conn.rollback()
                cur.close()
                raise ValueError("Modifié par un autre utilisateur.")
            hlp.conn.commit()
            cur.close()
        # Restaurer
        hlp._save_theme_config({
            "theme_id": orig.get("theme_id", "artizboard"),
            "primary_color": orig.get("primary_color", "#AAA"),
            "secondary_color": orig.get("secondary_color", ""),
            "accent_color": orig.get("accent_color", ""),
            "surface_color": orig.get("surface_color", ""),
            "font_heading": orig.get("font_heading", ""),
            "hero_title": orig.get("hero_title", ""),
            "hero_subtitle": orig.get("hero_subtitle", ""),
            "hero_button_text": orig.get("hero_button_text", ""),
            "hero_image_url": orig.get("hero_image_url", ""),
            "footer_text": orig.get("footer_text", ""),
            "seo_title_template": orig.get("seo_title_template", ""),
            "seo_description": orig.get("seo_description", ""),
            "facebook_url": orig.get("facebook_url", ""),
            "instagram_url": orig.get("instagram_url", ""),
            "whatsapp_number": orig.get("whatsapp_number", ""),
            "custom_css": orig.get("custom_css", ""),
        })

    def test_save_theme_preserves_facebook_url(self, hlp):
        """Vérifie que les URLs de réseaux sociaux sont bien sauvegardées."""
        _consolidate_theme(hlp)
        orig = hlp._fetch_theme_config()
        fb_value = "https://facebook.com/mapage_test"
        insta_value = "https://instagram.com/mapage_test"
        wa_value = "+22890123456"
        hlp._save_theme_config({
            "theme_id": orig.get("theme_id", "artizboard"),
            "primary_color": orig.get("primary_color", "#111"),
            "secondary_color": orig.get("secondary_color", "#222"),
            "accent_color": orig.get("accent_color", "#333"),
            "surface_color": orig.get("surface_color", "#444"),
            "font_heading": orig.get("font_heading", "Inter"),
            "hero_title": orig.get("hero_title", "T"),
            "hero_subtitle": orig.get("hero_subtitle", "S"),
            "hero_button_text": orig.get("hero_button_text", "B"),
            "hero_image_url": orig.get("hero_image_url", ""),
            "footer_text": "Footer test",
            "seo_title_template": orig.get("seo_title_template", "SEO"),
            "seo_description": orig.get("seo_description", "Desc"),
            "facebook_url": fb_value,
            "instagram_url": insta_value,
            "whatsapp_number": wa_value,
            "custom_css": orig.get("custom_css", ""),
        })
        tc = hlp._fetch_theme_config()
        assert tc["facebook_url"] == fb_value
        assert tc["instagram_url"] == insta_value
        assert tc["whatsapp_number"] == wa_value
        # Restaurer
        hlp._save_theme_config({
            "theme_id": orig.get("theme_id", "artizboard"),
            "primary_color": orig.get("primary_color", ""),
            "secondary_color": orig.get("secondary_color", ""),
            "accent_color": orig.get("accent_color", ""),
            "surface_color": orig.get("surface_color", ""),
            "font_heading": orig.get("font_heading", ""),
            "hero_title": orig.get("hero_title", ""),
            "hero_subtitle": orig.get("hero_subtitle", ""),
            "hero_button_text": orig.get("hero_button_text", ""),
            "hero_image_url": orig.get("hero_image_url", ""),
            "footer_text": orig.get("footer_text", ""),
            "seo_title_template": orig.get("seo_title_template", ""),
            "seo_description": orig.get("seo_description", ""),
            "facebook_url": orig.get("facebook_url", ""),
            "instagram_url": orig.get("instagram_url", ""),
            "whatsapp_number": orig.get("whatsapp_number", ""),
            "custom_css": orig.get("custom_css", ""),
        })


# ═══════════════════════════════════════════════════════
# Tests : Commandes
# ═══════════════════════════════════════════════════════

class TestCommandes:
    """Tests des commandes : lecture, filtrage par statut,
    changement de statut et lignes de commande."""

    def test_fetch_commandes_returns_list(self, hlp):
        """Vérifie que fetch_commandes retourne une liste (même vide)."""
        cmds = hlp._fetch_commandes()
        assert isinstance(cmds, list)

    def test_fetch_commandes_by_statut(self, hlp):
        """Vérifie que le filtre par statut fonctionne sur fetch_commandes."""
        all_cmds = hlp._fetch_commandes()
        if not all_cmds:
            pytest.skip("Aucune commande en base")
        statuts = set(c.get("statut") or "en_attente" for c in all_cmds)
        target = next(iter(statuts)) if statuts else "en_attente"
        filtered = hlp._fetch_commandes(statut=target)
        for c in filtered:
            actual = c.get("statut") or "en_attente"
            assert actual == target

    def test_change_statut_to_next(self, hlp):
        """Change le statut d'une commande et vérifie la mise à jour."""
        all_cmds = hlp._fetch_commandes()
        wait_cmds = hlp._fetch_commandes(statut="en_attente")
        if not wait_cmds:
            pytest.skip("Aucune commande 'en_attente' à tester")
        cmd = wait_cmds[0]
        old_statut = cmd.get("statut") or "en_attente"
        hlp._change_statut(cmd["id"], "en_preparation")
        updated = hlp._fetch_commandes(statut="en_preparation")
        found = any(c["id"] == cmd["id"] for c in updated)
        assert found
        # Restaurer le statut
        hlp._change_statut(cmd["id"], old_statut)

    def test_fetch_lignes_returns_data(self, hlp):
        """Vérifie que fetch_lignes retourne les lignes d'une commande."""
        all_cmds = hlp._fetch_commandes()
        if not all_cmds:
            pytest.skip("Aucune commande en base")
        cmd = all_cmds[0]
        lignes = hlp._fetch_lignes(cmd["id"])
        assert isinstance(lignes, list)
        for lc in lignes:
            assert "produit_nom" in lc
            assert "quantite" in lc
            assert "prix_unitaire" in lc

    def test_fetch_lignes_nonexistent_commande(self, hlp):
        """Vérifie que fetch_lignes retourne une liste vide pour une commande
        inexistante."""
        fake_id = str(uuid.uuid4())
        lignes = hlp._fetch_lignes(fake_id)
        assert lignes == []

    def test_change_statut_to_annule(self, hlp):
        """Annule une commande et vérifie qu'elle apparaît avec le statut
        'annule'."""
        wait_cmds = hlp._fetch_commandes(statut="en_attente")
        if not wait_cmds:
            # Essayer de créer une commande test
            pytest.skip("Aucune commande 'en_attente' à annuler")
        cmd = wait_cmds[0]
        old_statut = cmd.get("statut") or "en_attente"
        hlp._change_statut(cmd["id"], "annule")
        cancelled = hlp._fetch_commandes(statut="annule")
        found = any(c["id"] == cmd["id"] for c in cancelled)
        assert found
        # Restaurer
        hlp._change_statut(cmd["id"], old_statut)


# ═══════════════════════════════════════════════════════
# Tests : Auth via Admin (vérification croisée)
# ═══════════════════════════════════════════════════════

class TestAuthAdmin:
    """Vérifications auth dans le contexte admin : login, refresh token,
    listage et révocation d'appareils."""

    def test_admin_login_valid(self, hlp):
        """Vérifie que l'admin peut se connecter avec son mot de passe."""
        token, refresh, info = hlp.auth.login(
            "admin@larepublique.tg", "admin123"
        )
        assert isinstance(token, str)
        assert len(token) > 50
        assert info["role"] == "admin"
        assert info["etablissement_id"] == hlp.user["etablissement_id"]

    def test_admin_verify_token(self, hlp):
        """Vérifie que le token JWT de l'admin est valide."""
        token, _, _ = hlp.auth.login("admin@larepublique.tg", "admin123")
        claims = hlp.auth.verify_token(token)
        assert claims is not None
        assert claims["sub"] == hlp.user["id"]
        assert claims["role"] == "admin"

    def test_list_devices_returns_list(self, hlp):
        """Vérifie que list_devices retourne une liste."""
        devices = hlp.auth.list_devices(hlp.user["etablissement_id"])
        assert isinstance(devices, list)

    def test_revoke_device(self, hlp):
        """Vérifie qu'un appareil peut être révoqué."""
        devices = hlp.auth.list_devices(hlp.user["etablissement_id"])
        if not devices:
            pytest.skip("Aucun appareil à révoquer")
        dev = devices[0]
        hlp.auth.revoke_device(str(dev["id"]), hlp.user["id"])
        devices2 = hlp.auth.list_devices(hlp.user["etablissement_id"])
        assert not any(d["id"] == dev["id"] for d in devices2)
