"""Tests for dashboard_manager.py (KPIs, CSV, PDF)."""
import sys, pytest, os, csv, re
sys.path.insert(0, r'C:\projet')
from datetime import datetime, timedelta
from pathlib import Path


class TestDashboardKPI:
    """KPI queries."""

    def test_get_kpis(self, db_conn, etab_id):
        from dashboard_manager import DashboardManager
        dm = DashboardManager(db_conn, etab_id)
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        kpis = dm.get_kpis(week_ago, today)
        assert "ca_total" in kpis
        assert "nb_commandes" in kpis
        assert "panier_moyen" in kpis
        assert float(kpis.get("ca_total", 0)) >= 0

    def test_get_repartition_paiements(self, db_conn, etab_id):
        from dashboard_manager import DashboardManager
        dm = DashboardManager(db_conn, etab_id)
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        paiements = dm.get_repartition_paiements(week_ago, today)
        assert isinstance(paiements, list)
        for p in paiements:
            assert "moyen_paiement" in p

    def test_get_ca_par_jour(self, db_conn, etab_id):
        from dashboard_manager import DashboardManager
        dm = DashboardManager(db_conn, etab_id)
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        ca_jour = dm.get_ca_par_jour(week_ago, today)
        assert isinstance(ca_jour, list)
        for row in ca_jour:
            assert "jour" in row
            assert "ca" in row


class TestDashboardRestaurant:
    """Restaurant-specific dashboard."""

    def test_get_best_sellers(self, db_conn, etab_id):
        from dashboard_manager import DashboardManager
        dm = DashboardManager(db_conn, etab_id)
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        best = dm.get_best_sellers(week_ago, today, 5)
        assert isinstance(best, list)
        assert len(best) <= 5

    def test_get_repartition_service(self, db_conn, etab_id):
        from dashboard_manager import DashboardManager
        dm = DashboardManager(db_conn, etab_id)
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        service = dm.get_repartition_service(week_ago, today)
        assert isinstance(service, list)


class TestDashboardBoutique:
    """Boutique-specific dashboard."""

    def test_get_alertes_rupture(self, db_conn, etab_id):
        from dashboard_manager import DashboardManager
        dm = DashboardManager(db_conn, etab_id)
        alertes = dm.get_alertes_rupture()
        assert isinstance(alertes, list)

    def test_get_ca_par_categorie(self, db_conn, etab_id):
        from dashboard_manager import DashboardManager
        dm = DashboardManager(db_conn, etab_id)
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        cat_ca = dm.get_ca_par_categorie(week_ago, today)
        assert isinstance(cat_ca, list)


class TestCSVExport:
    """CSV export functionality."""

    def test_export_journal_financier(self, db_conn, etab_id, tmp_path):
        from dashboard_manager import DashboardManager
        dm = DashboardManager(db_conn, etab_id)
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        out = tmp_path / "test_journal_financier.csv"
        dm.export_csv_journal_financier(week_ago, today, str(out))
        assert out.exists()
        with open(out, encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=";")
            rows = list(reader)
            assert len(rows) > 0
            assert "Date" in rows[0]

    def test_export_journal_flux(self, db_conn, etab_id, tmp_path):
        from dashboard_manager import DashboardManager
        dm = DashboardManager(db_conn, etab_id)
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        out = tmp_path / "test_journal_flux.csv"
        dm.export_csv_journal_flux(week_ago, today, str(out))
        assert out.exists()


class TestPDFExport:
    """PDF report export."""

    def test_export_pdf_rapport(self, db_conn, etab_id, tmp_path):
        from dashboard_manager import DashboardManager
        dm = DashboardManager(db_conn, etab_id)
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        out = tmp_path / "test_rapport.pdf"
        export = dm.export_pdf_rapport(week_ago, today, str(out))
        assert export.exists()
        assert export.suffix == ".pdf"
        assert export.stat().st_size > 0
