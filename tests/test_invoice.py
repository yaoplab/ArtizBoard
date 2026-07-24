"""Tests for invoice_generator.py"""
import sys
import uuid

import pytest

sys.path.insert(0, r'C:\projet')

from invoice_generator import InvoiceGenerator


# ── Helpers ──

def _create_test_data(db_conn, admin_id, etab_id):
    """Create test commande + ligne_commande. Returns (cmd_id, prod_id, cat_id)."""
    cur = db_conn.cursor()

    cur.execute("SELECT id FROM categories WHERE deleted_at IS NULL LIMIT 1")
    cat = cur.fetchone()
    if cat:
        cat_id = str(cat[0])
    else:
        cat_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO categories (id, nom, etablissement_id, created_by) "
            "VALUES (%s, %s, %s, %s)",
            (cat_id, "Test Category", etab_id, admin_id),
        )

    cur.execute("SELECT id FROM produits WHERE deleted_at IS NULL LIMIT 1")
    prod = cur.fetchone()
    if prod:
        prod_id = str(prod[0])
    else:
        prod_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO produits (id, categorie_id, nom, prix, etablissement_id, created_by) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (prod_id, cat_id, "Test Product", 5000, etab_id, admin_id),
        )

    cmd_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO commandes (id, etablissement_id, total, montant_tva,
           moyen_paiement, statut_paiement, reference_client, created_by, staff_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (cmd_id, etab_id, 5000, 0, "cash", "paye", "TEST-001", admin_id, admin_id),
    )

    ligne_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO lignes_commande (id, commande_id, produit_id, quantite, prix_unitaire)
           VALUES (%s, %s, %s, %s, %s)""",
        (ligne_id, cmd_id, prod_id, 1, 5000),
    )

    db_conn.commit()
    cur.close()
    return cmd_id, prod_id, cat_id


def _cleanup_test_data(db_conn, cmd_id, prod_id=None, cat_id=None):
    """Delete test records in FK-safe order."""
    cur = db_conn.cursor()

    cur.execute("DELETE FROM factures WHERE commande_id = %s", (cmd_id,))
    cur.execute("DELETE FROM mouvements_stock WHERE commande_id = %s", (cmd_id,))
    cur.execute("DELETE FROM lignes_commande WHERE commande_id = %s", (cmd_id,))
    cur.execute("DELETE FROM commandes WHERE id = %s", (cmd_id,))

    if prod_id:
        cur.execute(
            "DELETE FROM produits WHERE id = %s AND nom = 'Test Product'",
            (prod_id,),
        )
    if cat_id:
        cur.execute(
            "DELETE FROM categories WHERE id = %s AND nom = 'Test Category'",
            (cat_id,),
        )

    db_conn.commit()
    cur.close()


# ── Tests ──

class TestInvoiceGenerator:
    """Invoice PDF generation tests."""

    def test_generate_invoice(self, db_conn, admin_id, etab_id):
        cmd_id, prod_id, cat_id = _create_test_data(db_conn, admin_id, etab_id)
        try:
            gen = InvoiceGenerator(db_conn)
            invoice_id, pdf_path, numero = gen.generate(cmd_id, created_by=admin_id)

            assert isinstance(invoice_id, str)
            assert uuid.UUID(invoice_id)
            assert numero.startswith("FAC-")
            assert pdf_path.suffix == ".pdf"
            assert pdf_path.exists()
            assert pdf_path.stat().st_size > 500
        finally:
            _cleanup_test_data(db_conn, cmd_id, prod_id, cat_id)

    def test_invoice_number_format(self, db_conn, admin_id, etab_id):
        cmd_id, prod_id, cat_id = _create_test_data(db_conn, admin_id, etab_id)
        try:
            gen = InvoiceGenerator(db_conn)
            _, _, numero = gen.generate(cmd_id, created_by=admin_id)

            parts = numero.split("-")
            assert len(parts) == 3, f"Expected 3 parts in '{numero}', got {len(parts)}"
            assert parts[0] == "FAC"
            assert len(parts[1]) == 8, f"Date part '{parts[1]}' should be 8 chars"
            assert parts[1].isdigit()
            assert len(parts[2]) == 5, f"Seq part '{parts[2]}' should be 5 chars"
            assert parts[2].isdigit()
        finally:
            _cleanup_test_data(db_conn, cmd_id, prod_id, cat_id)

    def test_generate_avoir(self, db_conn, admin_id, etab_id):
        cmd_id, prod_id, cat_id = _create_test_data(db_conn, admin_id, etab_id)
        try:
            gen = InvoiceGenerator(db_conn)
            facture_id, _, _ = gen.generate(cmd_id, created_by=admin_id)

            cmd_id2, prod_id2, cat_id2 = _create_test_data(db_conn, admin_id, etab_id)
            try:
                _, pdf_path2, numero_avoir = gen.generate_avoir(
                    cmd_id2, facture_id, created_by=admin_id
                )
                assert numero_avoir is not None
                assert numero_avoir.startswith("FAC-")
                assert pdf_path2.suffix == ".pdf"
                assert pdf_path2.exists()

                cur = db_conn.cursor()
                cur.execute(
                    "SELECT type_facture, facture_parent_id FROM factures WHERE commande_id = %s",
                    (cmd_id2,),
                )
                row = cur.fetchone()
                cur.close()
                assert row is not None
                assert row[0] == "avoir"
                assert str(row[1]) == facture_id
            finally:
                _cleanup_test_data(db_conn, cmd_id2, prod_id2, cat_id2)
        finally:
            _cleanup_test_data(db_conn, cmd_id, prod_id, cat_id)

    def test_offline_invoice_number(self, db_conn, admin_id, etab_id):
        gen = InvoiceGenerator(db_conn, offline_device_id="42")
        numero = gen._next_numero_offline()
        parts = numero.split("-")
        assert len(parts) == 4, f"Expected 4 parts in offline format, got {len(parts)}: {numero}"
        assert parts[0] == "FAC"
        assert len(parts[1]) == 8 and parts[1].isdigit()
        assert parts[2] == "DEV42"
        assert len(parts[3]) == 5 and parts[3].isdigit()

        cmd_id, prod_id, cat_id = _create_test_data(db_conn, admin_id, etab_id)
        try:
            _, _, numero2 = gen.generate(cmd_id, created_by=admin_id)
            assert numero2.startswith("FAC-")
        finally:
            _cleanup_test_data(db_conn, cmd_id, prod_id, cat_id)


class TestReceiptText:
    """Text receipt tests."""

    def test_get_receipt_text(self, db_conn, admin_id, etab_id):
        cmd_id, prod_id, cat_id = _create_test_data(db_conn, admin_id, etab_id)
        try:
            gen = InvoiceGenerator(db_conn)
            gen.generate(cmd_id, created_by=admin_id)
            text = gen.get_receipt_text(cmd_id)

            assert isinstance(text, str)
            assert len(text) > 50
            assert "TOTAL" in text.upper()
        finally:
            _cleanup_test_data(db_conn, cmd_id, prod_id, cat_id)
