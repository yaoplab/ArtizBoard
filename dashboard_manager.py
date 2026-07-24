"""ArtizBoard — Dashboard Manager (Livrable C)

Analyse financière, suivi des stocks, classements restaurant,
exports CSV et rapport PDF synthétique.

Usage:
    from dashboard_manager import DashboardManager
    dm = DashboardManager(conn, etablissement_id)
    kpis = dm.get_kpis("2026-07-01", "2026-07-15")
    dm.export_csv_financier("2026-07-01", "2026-07-15", "rapport.csv")
"""

import csv
import logging
import os
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Optional

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as PgConnection

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image, PageBreak, HRFlowable, KeepTogether,
)

logger = logging.getLogger("dashboard_manager")

# ── Constants ──
EXPORT_DIR = Path(__file__).parent / "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

PRIMARY = HexColor("#1565C0")
SECONDARY = HexColor("#455A64")
GOOD = HexColor("#2E7D32")
BAD = HexColor("#C62828")
WARN = HexColor("#E65100")
LIGHT_BG = HexColor("#F5F7FA")
BORDER = HexColor("#B0BEC5")

STYLE_H1 = ParagraphStyle("DH1", fontSize=18, leading=22, fontName="Helvetica-Bold",
                          textColor=PRIMARY, spaceAfter=10)
STYLE_H2 = ParagraphStyle("DH2", fontSize=13, leading=17, fontName="Helvetica-Bold",
                          textColor=SECONDARY, spaceAfter=6, spaceBefore=12)
STYLE_BODY = ParagraphStyle("DBody", fontSize=10, leading=13, fontName="Helvetica")
STYLE_BOLD = ParagraphStyle("DBold", fontSize=10, leading=13, fontName="Helvetica-Bold")
STYLE_SMALL = ParagraphStyle("DSmall", fontSize=8, leading=10, fontName="Helvetica",
                             textColor=SECONDARY)
STYLE_RIGHT = ParagraphStyle("DRight", fontSize=10, leading=13, fontName="Helvetica",
                             alignment=TA_RIGHT)
STYLE_CENTER = ParagraphStyle("DCenter", fontSize=10, leading=13, fontName="Helvetica",
                              alignment=TA_CENTER)
STYLE_KPI_VALUE = ParagraphStyle("DKPI", fontSize=28, leading=32, fontName="Helvetica-Bold",
                                 textColor=PRIMARY, alignment=TA_CENTER)
STYLE_KPI_LABEL = ParagraphStyle("DKPIL", fontSize=8, leading=10, fontName="Helvetica",
                                 textColor=SECONDARY, alignment=TA_CENTER)


class DashboardManager:
    """Agrégation de données, KPIs et exports."""

    def __init__(self, conn: PgConnection, etablissement_id: str):
        self.conn = conn
        self.etablissement_id = etablissement_id

    def _query(self, sql: str, params: tuple = ()) -> list[dict]:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def _query_one(self, sql: str, params: tuple = ()) -> dict:
        rows = self._query(sql, params)
        return rows[0] if rows else {}

    # ═══════════════════════════════════════════════════════════
    #  KPI — Indicateurs clés
    # ═══════════════════════════════════════════════════════════

    def get_kpis(self, date_debut: str, date_fin: str) -> dict:
        """Chiffre d'affaires, panier moyen, nombre de commandes (période)."""
        return self._query_one("""
            SELECT
                COALESCE(SUM(total), 0)::numeric AS ca_total,
                COUNT(*)::int AS nb_commandes,
                CASE WHEN COUNT(*) > 0
                     THEN (SUM(total) / COUNT(*))::numeric
                     ELSE 0 END AS panier_moyen
            FROM commandes
            WHERE statut IN ('pret', 'livre')
              AND statut_paiement = 'paye'
              AND etablissement_id = %s
              AND created_at >= %s
              AND created_at < %s::date + 1
              AND deleted_at IS NULL
        """, (self.etablissement_id, date_debut, date_fin))

    def get_ca_par_jour(self, date_debut: str, date_fin: str) -> list[dict]:
        """CA journalier sur la période."""
        return self._query("""
            SELECT
                DATE(created_at) AS jour,
                SUM(total)::numeric AS ca,
                COUNT(*)::int AS nb_commandes
            FROM commandes
            WHERE statut IN ('pret', 'livre')
              AND statut_paiement = 'paye'
              AND etablissement_id = %s
              AND created_at >= %s
              AND created_at < %s::date + 1
              AND deleted_at IS NULL
            GROUP BY DATE(created_at)
            ORDER BY jour
        """, (self.etablissement_id, date_debut, date_fin))

    def get_repartition_paiements(self, date_debut: str, date_fin: str) -> list[dict]:
        """Répartition des encaissements par moyen de paiement."""
        return self._query("""
            SELECT
                moyen_paiement,
                COUNT(*)::int AS nb,
                SUM(total)::numeric AS ca
            FROM commandes
            WHERE statut_paiement = 'paye'
              AND etablissement_id = %s
              AND created_at >= %s
              AND created_at < %s::date + 1
              AND deleted_at IS NULL
            GROUP BY moyen_paiement
            ORDER BY ca DESC
        """, (self.etablissement_id, date_debut, date_fin))

    # ═══════════════════════════════════════════════════════════
    #  Boutique — Stocks & Mouvements
    # ═══════════════════════════════════════════════════════════

    def get_alertes_rupture(self) -> list[dict]:
        """Produits avec stock <= seuil d'alerte."""
        return self._query("""
            SELECT
                p.id, p.nom, p.stock, p.stock_alerte,
                c.nom AS categorie_nom, p.prix
            FROM produits p
            JOIN categories c ON p.categorie_id = c.id
            WHERE p.etablissement_id = %s
              AND p.deleted_at IS NULL
              AND c.deleted_at IS NULL
              AND p.stock <= p.stock_alerte
            ORDER BY p.stock ASC
        """, (self.etablissement_id,))

    def get_mouvements_stock(self, date_debut: str, date_fin: str) -> list[dict]:
        """Journal des mouvements de stock (appro, ventes, pertes)."""
        return self._query("""
            SELECT
                ms.type_mouvement,
                ms.quantite,
                ms.motif,
                ms.created_at,
                p.nom AS produit_nom,
                p.id AS produit_id
            FROM mouvements_stock ms
            JOIN produits p ON ms.produit_id = p.id
            WHERE p.etablissement_id = %s
              AND ms.created_at >= %s
              AND ms.created_at < %s::date + 1
            ORDER BY ms.created_at DESC
        """, (self.etablissement_id, date_debut, date_fin))

    def get_ca_par_categorie(self, date_debut: str, date_fin: str) -> list[dict]:
        """CA par catégorie de produit."""
        return self._query("""
            SELECT
                c.nom AS categorie,
                COUNT(DISTINCT lc.id)::int AS nb_lignes,
                SUM(lc.quantite)::int AS total_quantite,
                SUM(lc.quantite * lc.prix_unitaire)::numeric AS ca
            FROM lignes_commande lc
            JOIN produits p ON lc.produit_id = p.id
            JOIN categories c ON p.categorie_id = c.id
            JOIN commandes cmd ON lc.commande_id = cmd.id
            WHERE cmd.statut IN ('pret', 'livre')
              AND cmd.statut_paiement = 'paye'
              AND p.etablissement_id = %s
              AND cmd.created_at >= %s
              AND cmd.created_at < %s::date + 1
              AND lc.deleted_at IS NULL
              AND p.deleted_at IS NULL
              AND cmd.deleted_at IS NULL
            GROUP BY c.nom
            ORDER BY ca DESC
        """, (self.etablissement_id, date_debut, date_fin))

    # ═══════════════════════════════════════════════════════════
    #  Restaurant — Volumes & Palmarès
    # ═══════════════════════════════════════════════════════════

    def get_volume_plats(self, date_debut: str, date_fin: str) -> list[dict]:
        """Volume de plats vendus (tous, triés par quantité)."""
        return self._query("""
            SELECT
                p.nom,
                p.id AS produit_id,
                SUM(lc.quantite)::int AS total_quantite,
                COUNT(DISTINCT lc.commande_id)::int AS nb_commandes,
                SUM(lc.quantite * lc.prix_unitaire)::numeric AS ca_genere
            FROM lignes_commande lc
            JOIN produits p ON lc.produit_id = p.id
            JOIN commandes c ON lc.commande_id = c.id
            WHERE c.statut IN ('pret', 'livre')
              AND c.statut_paiement = 'paye'
              AND c.etablissement_id = %s
              AND c.created_at >= %s
              AND c.created_at < %s::date + 1
              AND c.deleted_at IS NULL
              AND lc.deleted_at IS NULL
              AND p.deleted_at IS NULL
            GROUP BY p.id, p.nom
            ORDER BY total_quantite DESC
        """, (self.etablissement_id, date_debut, date_fin))

    def get_best_sellers(self, date_debut: str, date_fin: str,
                         limit: int = 5) -> list[dict]:
        """Top N plats les plus vendus."""
        plats = self.get_volume_plats(date_debut, date_fin)
        return plats[:limit]

    def get_flops(self, date_debut: str, date_fin: str,
                  limit: int = 5) -> list[dict]:
        """Top N plats les moins vendus (parmi ceux qui ont été vendus)."""
        plats = self.get_volume_plats(date_debut, date_fin)
        return list(reversed(plats[-limit:])) if len(plats) >= limit else []

    def get_repartition_service(self, date_debut: str, date_fin: str) -> list[dict]:
        """Répartition sur place / emporter / livraison."""
        return self._query("""
            SELECT
                type_service,
                COUNT(*)::int AS nb,
                SUM(total)::numeric AS ca
            FROM commandes
            WHERE etablissement_id = %s
              AND created_at >= %s
              AND created_at < %s::date + 1
              AND deleted_at IS NULL
            GROUP BY type_service
            ORDER BY nb DESC
        """, (self.etablissement_id, date_debut, date_fin))

    # ═══════════════════════════════════════════════════════════
    #  Export CSV
    # ═══════════════════════════════════════════════════════════

    def export_csv_journal_financier(self, date_debut: str, date_fin: str,
                                     output_path: str = "") -> Path:
        """Export CSV : journal financier."""
        rows = self._query("""
            SELECT
                DATE(c.created_at) AS date_transaction,
                c.id AS commande_id,
                e.type AS type_etablissement,
                c.total,
                c.montant_tva,
                c.moyen_paiement
            FROM commandes c
            JOIN etablissements e ON c.etablissement_id = e.id
            WHERE c.etablissement_id = %s
              AND c.created_at >= %s
              AND c.created_at < %s::date + 1
              AND c.deleted_at IS NULL
              AND c.statut_paiement = 'paye'
            ORDER BY c.created_at
        """, (self.etablissement_id, date_debut, date_fin))

        return self._write_csv(
            rows,
            ["Date", "ID Commande", "Type Établissement", "Montant TTC",
             "TVA", "Moyen Paiement"],
            output_path or str(EXPORT_DIR / f"journal_financier_{date_debut.replace('-','')}.csv"),
        )

    def export_csv_journal_flux(self, date_debut: str, date_fin: str,
                                output_path: str = "") -> Path:
        """Export CSV : journal des flux matériels."""
        rows = self._query("""
            SELECT
                DATE(ms.created_at) AS date_flux,
                p.nom AS produit,
                ms.type_mouvement,
                ms.quantite,
                ms.motif
            FROM mouvements_stock ms
            JOIN produits p ON ms.produit_id = p.id
            WHERE p.etablissement_id = %s
              AND ms.created_at >= %s
              AND ms.created_at < %s::date + 1
            ORDER BY ms.created_at
        """, (self.etablissement_id, date_debut, date_fin))

        return self._write_csv(
            rows,
            ["Date", "Produit", "Type Flux", "Quantité", "Motif"],
            output_path or str(EXPORT_DIR / f"journal_flux_{date_debut.replace('-','')}.csv"),
        )

    def _write_csv(self, rows: list[dict], headers: list[str],
                   path: str) -> Path:
        filepath = Path(path)
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=";")
            writer.writeheader()

            type_labels = {
                "entree_appro": "Entrée appro",
                "sortie_vente": "Sortie vente",
                "sortie_perte": "Sortie perte",
                "sortie_remboursement": "Sortie remboursement",
                "ajustement": "Ajustement",
                "boutique_reelle": "Boutique Réelle",
                "boutique_virtuelle": "Boutique Virtuelle",
                "restaurant": "Restaurant",
            }

            for row in rows:
                clean = {}
                for h in headers:
                    val = row.get(h.lower().replace(" ", "_"), "")
                    val = val or ""
                    if h == "Type Flux" or h == "Type Établissement":
                        val = type_labels.get(str(val), val)
                    clean[h] = val
                writer.writerow(clean)

        logger.info(f"CSV exporté → {filepath}")
        return filepath

    # ═══════════════════════════════════════════════════════════
    #  Export PDF — Rapport synthétique
    # ═══════════════════════════════════════════════════════════

    def export_pdf_rapport(self, date_debut: str, date_fin: str,
                           output_path: str = "") -> Path:
        """Export PDF : rapport synthétique avec KPIs, tableaux, palmarès."""
        filepath = Path(output_path or str(
            EXPORT_DIR / f"rapport_{date_debut.replace('-','')}_{date_fin.replace('-','')}.pdf"
        ))

        # Fetch all data
        kpis = self.get_kpis(date_debut, date_fin)
        ca_jour = self.get_ca_par_jour(date_debut, date_fin)
        paiements = self.get_repartition_paiements(date_debut, date_fin)
        alertes = self.get_alertes_rupture()
        mouvements = self.get_mouvements_stock(date_debut, date_fin)
        best = self.get_best_sellers(date_debut, date_fin)
        flops = self.get_flops(date_debut, date_fin)
        cat_ca = self.get_ca_par_categorie(date_debut, date_fin)
        service = self.get_repartition_service(date_debut, date_fin)

        # Build PDF
        doc = SimpleDocTemplate(
            str(filepath), pagesize=A4,
            leftMargin=15 * mm, rightMargin=15 * mm,
            topMargin=15 * mm, bottomMargin=15 * mm,
            title=f"Rapport {date_debut} → {date_fin}",
            author="ArtizBoard",
        )

        story = []

        # Title
        story.append(Paragraph(f"Rapport d'activité", STYLE_H1))
        story.append(Paragraph(
            f"Période : {date_debut} au {date_fin}  —  Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            STYLE_SMALL,
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
        story.append(Spacer(1, 8 * mm))

        # KPI Cards
        story.extend(self._build_kpi_section(kpis))
        story.append(Spacer(1, 6 * mm))

        # CA par jour — table
        if ca_jour:
            story.append(Paragraph("Chiffre d'affaires journalier", STYLE_H2))
            story.extend(self._build_ca_table(ca_jour))
            story.append(Spacer(1, 6 * mm))

        # Paiements
        if paiements:
            story.append(Paragraph("Répartition des paiements", STYLE_H2))
            story.extend(self._build_paiement_table(paiements))
            story.append(Spacer(1, 6 * mm))

        # Restaurant : Best-sellers + Flops
        if best or flops:
            story.append(Paragraph("Palmarès cuisine", STYLE_H2))
            if best:
                story.extend(self._build_ranking_table("Top 5 — Best-sellers", best, GOOD))
            if flops:
                story.extend(self._build_ranking_table("Top 5 — Moins vendus", flops, WARN))
            story.append(Spacer(1, 6 * mm))

        # Service type (restaurant)
        if service:
            story.append(Paragraph("Répartition par type de service", STYLE_H2))
            story.extend(self._build_service_table(service))
            story.append(Spacer(1, 6 * mm))

        # Boutique : alertes rupture
        if alertes:
            story.append(Paragraph("Alertes de rupture de stock", STYLE_H2))
            story.extend(self._build_rupture_table(alertes))
            story.append(Spacer(1, 6 * mm))

        # Mouvements stock
        if mouvements:
            story.append(Paragraph("Mouvements de stock", STYLE_H2))
            story.extend(self._build_mouvements_table(mouvements[:20]))

        doc.build(story)
        logger.info(f"Rapport PDF exporté → {filepath}")
        return filepath

    # ── PDF section builders ──

    def _build_kpi_section(self, kpis: dict) -> list:
        ca = float(kpis.get("ca_total", 0))
        nb = int(kpis.get("nb_commandes", 0))
        pm = float(kpis.get("panier_moyen", 0))

        data = [[
            [Paragraph(f"{ca:,.0f} F", STYLE_KPI_VALUE),
             Paragraph("Chiffre d'affaires", STYLE_KPI_LABEL)],
            [Paragraph(str(nb), STYLE_KPI_VALUE),
             Paragraph("Commandes", STYLE_KPI_LABEL)],
            [Paragraph(f"{pm:,.0f} F", STYLE_KPI_VALUE),
             Paragraph("Panier moyen", STYLE_KPI_LABEL)],
        ]]

        table = Table(data, colWidths=[60 * mm] * 3)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ]))
        return [table]

    def _build_ca_table(self, rows: list[dict]) -> list:
        data = []
        data.append([
            Paragraph("<b>Jour</b>", STYLE_BOLD),
            Paragraph("<b>CA</b>", STYLE_BOLD),
            Paragraph("<b>Nb Cdes</b>", STYLE_BOLD),
        ])
        for r in rows:
            jour = str(r.get("jour", ""))
            if isinstance(jour, str) and len(jour) > 10:
                jour = jour[:10]
            data.append([
                Paragraph(jour, STYLE_BODY),
                Paragraph(f"{float(r['ca']):,.0f} F", STYLE_RIGHT),
                Paragraph(str(r["nb_commandes"]), STYLE_CENTER),
            ])

        return self._styled_table(data, [70 * mm, 50 * mm, 40 * mm])

    def _build_paiement_table(self, rows: list[dict]) -> list:
        data = [[
            Paragraph("<b>Moyen</b>", STYLE_BOLD),
            Paragraph("<b>Nb</b>", STYLE_BOLD),
            Paragraph("<b>CA</b>", STYLE_BOLD),
        ]]
        labels = {"cash": "Espèces", "tmoney": "TMoney", "flooz": "Flooz"}
        for r in rows:
            data.append([
                Paragraph(labels.get(r.get("moyen_paiement", ""), r.get("moyen_paiement", "—")), STYLE_BODY),
                Paragraph(str(r["nb"]), STYLE_CENTER),
                Paragraph(f"{float(r['ca']):,.0f} F", STYLE_RIGHT),
            ])
        return self._styled_table(data, [60 * mm, 50 * mm, 50 * mm])

    def _build_ranking_table(self, title: str, rows: list[dict],
                              color=PRIMARY) -> list:
        elements = [Paragraph(title, STYLE_H2), Spacer(1, 2 * mm)]
        data = [[
            Paragraph("<b>#</b>", STYLE_BOLD),
            Paragraph("<b>Plat</b>", STYLE_BOLD),
            Paragraph("<b>Qté</b>", STYLE_BOLD),
            Paragraph("<b>CA</b>", STYLE_BOLD),
        ]]
        for i, r in enumerate(rows, 1):
            data.append([
                Paragraph(f"<font color='{color}'>{i}</font>", STYLE_CENTER),
                Paragraph(r.get("nom", "—"), STYLE_BODY),
                Paragraph(str(r["total_quantite"]), STYLE_CENTER),
                Paragraph(f"{float(r['ca_genere']):,.0f} F", STYLE_RIGHT),
            ])
        elements.extend(self._styled_table(data, [12 * mm, 80 * mm, 28 * mm, 40 * mm]))
        return elements

    def _build_rupture_table(self, rows: list[dict]) -> list:
        data = [[
            Paragraph("<b>Produit</b>", STYLE_BOLD),
            Paragraph("<b>Catégorie</b>", STYLE_BOLD),
            Paragraph("<b>Stock</b>", STYLE_BOLD),
            Paragraph("<b>Alerte</b>", STYLE_BOLD),
        ]]
        for r in rows:
            stock = int(r["stock"])
            couleur = BAD if stock == 0 else WARN
            data.append([
                Paragraph(r["nom"], STYLE_BODY),
                Paragraph(r.get("categorie_nom", "—"), STYLE_BODY),
                Paragraph(f"<font color='{couleur}'>{stock}</font>", STYLE_CENTER),
                Paragraph(str(r["stock_alerte"]), STYLE_CENTER),
            ])
        return self._styled_table(data, [60 * mm, 40 * mm, 20 * mm, 20 * mm])

    def _build_mouvements_table(self, rows: list[dict]) -> list:
        type_labels = {
            "entree_appro": "+ Appro",
            "sortie_vente": "− Vente",
            "sortie_perte": "− Perte",
            "sortie_remboursement": "− Rembours.",
            "ajustement": "± Ajust.",
        }
        data = [[
            Paragraph("<b>Date</b>", STYLE_BOLD),
            Paragraph("<b>Produit</b>", STYLE_BOLD),
            Paragraph("<b>Type</b>", STYLE_BOLD),
            Paragraph("<b>Qté</b>", STYLE_BOLD),
            Paragraph("<b>Motif</b>", STYLE_BOLD),
        ]]
        for r in rows:
            date_str = str(r.get("created_at", ""))[:10]
            couleur = GOOD if "entree" in (r["type_mouvement"] or "") else BAD
            data.append([
                Paragraph(date_str, STYLE_SMALL),
                Paragraph(r["produit_nom"], STYLE_BODY),
                Paragraph(f"<font color='{couleur}'>{type_labels.get(r['type_mouvement'], r['type_mouvement'])}</font>",
                         STYLE_BODY),
                Paragraph(str(r["quantite"]), STYLE_CENTER),
                Paragraph(r.get("motif") or "", STYLE_SMALL),
            ])
        return self._styled_table(data, [28 * mm, 48 * mm, 30 * mm, 14 * mm, 40 * mm])

    def _build_service_table(self, rows: list[dict]) -> list:
        labels = {"sur_place": "Sur place", "emporter": "À emporter", "livraison": "Livraison"}
        data = [[
            Paragraph("<b>Type</b>", STYLE_BOLD),
            Paragraph("<b>Nb</b>", STYLE_BOLD),
            Paragraph("<b>CA</b>", STYLE_BOLD),
        ]]
        for r in rows:
            data.append([
                Paragraph(labels.get(r["type_service"], r["type_service"]), STYLE_BODY),
                Paragraph(str(r["nb"]), STYLE_CENTER),
                Paragraph(f"{float(r['ca']):,.0f} F", STYLE_RIGHT),
            ])
        return self._styled_table(data, [60 * mm, 50 * mm, 50 * mm])

    def _styled_table(self, data: list, col_widths: list,
                      header_rows: int = 1) -> list:
        t = Table(data, colWidths=col_widths, repeatRows=header_rows)
        style_cmds = [
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]
        if header_rows > 0:
            style_cmds.extend([
                ("BACKGROUND", (0, 0), (-1, header_rows - 1), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), white),
            ])
        for i in range(header_rows, len(data), 2):
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_BG))
        t.setStyle(TableStyle(style_cmds))
        return [t]
