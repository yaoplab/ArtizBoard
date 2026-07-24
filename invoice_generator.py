"""ArtizBoard — Invoice Generator (Livrable B)

Génération de factures PDF (A4) et tickets thermiques (ESC/POS).

Usage:
    from invoice_generator import InvoiceGenerator
    gen = InvoiceGenerator(conn)
    invoice = gen.generate(commande_id, created_by=user_id)
    # → (invoice_id, pdf_path, numero_facture)
    gen.print_thermal(invoice_id, printer_ip="192.168.1.100")

Formats de numéro :
    Normal   : FAC-YYYYMMDD-00001 (via SEQUENCE PostgreSQL)
    Offline  : FAC-YYYYMMDD-DEV3-00001 (si serveur injoignable, renuméroté à la synchro)
"""

import io
import logging
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional, Tuple

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as PgConnection

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, grey, white, PCMYKColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image, PageBreak, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable

from escpos.printer import Network as EscposNetwork

logger = logging.getLogger("invoice_generator")

# ── Constants ──
PDF_DIR = Path(__file__).parent / "factures"
INVOICE_DIR = PDF_DIR
PRIMARY_COLOR = HexColor("#1565C0")
SECONDARY_COLOR = HexColor("#455A64")
LIGHT_BG = HexColor("#F5F7FA")
BORDER_COLOR = HexColor("#B0BEC5")
ERROR_COLOR = HexColor("#C62828")


# ── Paragraph styles ──

STYLE_TITLE = ParagraphStyle(
    "InvoiceTitle", fontSize=20, leading=24, textColor=PRIMARY_COLOR,
    fontName="Helvetica-Bold", spaceAfter=6,
)
STYLE_H2 = ParagraphStyle(
    "InvoiceH2", fontSize=14, leading=18, textColor=SECONDARY_COLOR,
    fontName="Helvetica-Bold", spaceAfter=4,
)
STYLE_BODY = ParagraphStyle(
    "InvoiceBody", fontSize=10, leading=14, textColor=black,
    fontName="Helvetica", spaceAfter=2,
)
STYLE_BODY_BOLD = ParagraphStyle(
    "InvoiceBodyBold", fontSize=10, leading=14, textColor=black,
    fontName="Helvetica-Bold", spaceAfter=2,
)
STYLE_SMALL = ParagraphStyle(
    "InvoiceSmall", fontSize=8, leading=10, textColor=grey,
    fontName="Helvetica", spaceAfter=1,
)
STYLE_CENTER = ParagraphStyle(
    "InvoiceCenter", fontSize=10, leading=14, textColor=black,
    fontName="Helvetica", alignment=TA_CENTER,
)
STYLE_RIGHT = ParagraphStyle(
    "InvoiceRight", fontSize=10, leading=14, textColor=black,
    fontName="Helvetica", alignment=TA_RIGHT,
)
STYLE_FOOTER = ParagraphStyle(
    "InvoiceFooter", fontSize=9, leading=12, textColor=SECONDARY_COLOR,
    fontName="Helvetica-Oblique", alignment=TA_CENTER,
)
STYLE_WATERMARK = ParagraphStyle(
    "Watermark", fontSize=72, leading=72, textColor=HexColor("#CC0000"),
    fontName="Helvetica-Bold", alignment=TA_CENTER, alpha=0.15,
)


class InvoiceGenerator:
    """Generates PDF invoices and thermal receipts."""

    def __init__(self, conn: PgConnection, offline_device_id: str = ""):
        self.conn = conn
        self.offline_device_id = offline_device_id
        os.makedirs(INVOICE_DIR, exist_ok=True)

    # ── Invoice number generation ──

    def _next_numero(self) -> str:
        """Generate next invoice number: FAC-YYYYMMDD-XXXXX."""
        today = datetime.now().strftime("%Y%m%d")
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT nextval('seq_numero_facture')")
            seq = cur.fetchone()[0]
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            # Fallback if sequence doesn't exist
            seq = int(datetime.now().timestamp() * 1000) % 100000
        finally:
            cur.close()
        return f"FAC-{today}-{seq:05d}"

    def _next_numero_offline(self) -> str:
        """Offline invoice number: FAC-YYYYMMDD-DEV{ID}-XXXXX."""
        today = datetime.now().strftime("%Y%m%d")
        dev = self.offline_device_id or "00"
        seq = int(datetime.now().timestamp() * 1000) % 100000
        return f"FAC-{today}-DEV{dev}-{seq:05d}"

    def _is_offline(self) -> bool:
        """Check if we can reach the PostgreSQL server sequence."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            return False
        except Exception:
            return True

    # ── Data fetching ──

    def _fetch_commande(self, commande_id: str) -> dict:
        """Fetch full order data."""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT c.*, e.nom AS etablissement_nom, e.logo_url, e.adresse,
                   e.telephone, e.email, e.site_web, e.mission,
                   e.moyens_paiement_acceptes, e.taux_tva_defaut
            FROM commandes c
            JOIN etablissements e ON c.etablissement_id = e.id
            WHERE c.id = %s AND c.deleted_at IS NULL
        """, (commande_id,))
        cmd = cur.fetchone()
        if not cmd:
            cur.close()
            raise ValueError(f"Commande {commande_id} introuvable")
        cmd = dict(cmd)

        # Lignes
        cur.execute("""
            SELECT lc.*, p.nom AS produit_nom
            FROM lignes_commande lc
            JOIN produits p ON lc.produit_id = p.id
            WHERE lc.commande_id = %s AND lc.deleted_at IS NULL
            ORDER BY lc.created_at
        """, (commande_id,))
        cmd["lignes"] = [dict(r) for r in cur.fetchall()]

        # Client
        if cmd.get("client_id"):
            cur.execute(
                "SELECT nom, email, telephone FROM utilisateurs WHERE id = %s",
                (cmd["client_id"],),
            )
            client = cur.fetchone()
            if client:
                cmd["client_nom"] = client["nom"]
                cmd["client_email"] = client.get("email") or ""
                cmd["client_telephone"] = client.get("telephone") or ""

        cur.close()
        return cmd

    # ── PDF generation ──

    def generate(self, commande_id: str, created_by: str = "",
                 type_facture: str = "facture",
                 facture_parent_id: str = None) -> Tuple[str, Path, str]:
        """Generate PDF invoice. Returns (invoice_id, pdf_path, numero_facture)."""

        cmd = self._fetch_commande(commande_id)
        offline = self._is_offline()
        numero = self._next_numero_offline() if offline else self._next_numero()

        invoice_id = str(uuid.uuid4())
        filename = f"{numero}.pdf"
        pdf_path = INVOICE_DIR / filename

        # ── Build PDF ──
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            title=numero,
            author="ArtizBoard",
        )

        story = []
        styles = self._build_styles()
        story.extend(self._build_header(cmd, numero, type_facture))
        story.append(Spacer(1, 10 * mm))
        story.extend(self._build_lines_table(cmd))
        story.append(Spacer(1, 8 * mm))
        story.extend(self._build_totals(cmd))
        story.append(Spacer(1, 6 * mm))
        story.extend(self._build_payment_info(cmd))
        story.append(Spacer(1, 8 * mm))
        story.extend(self._build_footer(cmd))

        # Watermark for AVOIR
        if type_facture == "avoir":
            story.insert(0, Spacer(1, 40 * mm))
            story.insert(0, Paragraph("AVOIR / NOTE DE CRÉDIT", STYLE_WATERMARK))

        doc.build(story)

        # ── Save to DB ──
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO factures (id, commande_id, type_facture, facture_parent_id,
                                  numero_facture, date_emission, pdf_path_local, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (commande_id) DO UPDATE SET
                type_facture = EXCLUDED.type_facture,
                numero_facture = EXCLUDED.numero_facture,
                pdf_path_local = EXCLUDED.pdf_path_local,
                updated_at = NOW()
            RETURNING id
        """, (
            invoice_id, commande_id, type_facture,
            facture_parent_id, numero,
            datetime.now(timezone.utc), str(pdf_path), created_by,
        ))
        self.conn.commit()
        cur.close()

        logger.info(f"Facture {numero} générée → {pdf_path}")
        return invoice_id, pdf_path, numero

    def generate_avoir(self, commande_id: str, facture_parent_id: str,
                       created_by: str = "") -> Tuple[str, Path, str]:
        """Generate credit note (avoir)."""
        return self.generate(
            commande_id=commande_id,
            created_by=created_by,
            type_facture="avoir",
            facture_parent_id=facture_parent_id,
        )

    # ── PDF sections ──

    def _build_styles(self):
        return {
            "title": STYLE_TITLE,
            "h2": STYLE_H2,
            "body": STYLE_BODY,
            "bold": STYLE_BODY_BOLD,
            "small": STYLE_SMALL,
            "center": STYLE_CENTER,
            "right": STYLE_RIGHT,
            "footer": STYLE_FOOTER,
        }

    def _build_header(self, cmd: dict, numero: str, type_facture: str) -> list:
        """Build invoice header with logo and establishment info."""
        etab = cmd.get("etablissement_nom", "Établissement")
        adresse = cmd.get("adresse", "")
        tel = cmd.get("telephone", "")
        email = cmd.get("email", "")
        site = cmd.get("site_web", "")

        # Logo placeholder (or real logo if path exists)
        logo_path = cmd.get("logo_url", "")
        logo = None
        if logo_path and os.path.exists(logo_path):
            logo = Image(logo_path, width=40 * mm, height=20 * mm)

        header_data = []
        if logo:
            header_data.append([logo, ""])

        header_data.append([
            Paragraph(f"<b>{etab}</b>", STYLE_BODY_BOLD),
            Paragraph(f"<b>{'AVOIR' if type_facture == 'avoir' else 'FACTURE'}</b>", STYLE_TITLE),
        ])
        header_data.append([
            Paragraph(f"{adresse}<br/>{tel}<br/>{email}<br/>{site}", STYLE_SMALL),
            Paragraph(f"N° {numero}", STYLE_H2),
        ])

        # Date + client
        date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        client_nom = cmd.get("client_nom")
        ref = cmd.get("reference_client", "")
        client_line = f"Date : {date_str}"
        if client_nom:
            client_line += f"<br/>Client : {client_nom}"
        elif ref:
            client_line += f"<br/>Référence : {ref}"
        else:
            client_line += "<br/>Client au comptoir"

        if type_facture == "avoir" and cmd.get("facture_parent_id"):
            client_line += f"<br/>Facture d'origine : {cmd.get('facture_parent_id', '')}"

        header_data.append([
            Paragraph(client_line, STYLE_BODY),
            "",
        ])

        table = Table(header_data, colWidths=[120 * mm, 50 * mm])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        return [
            HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR),
            Spacer(1, 4 * mm),
            table,
            HRFlowable(width="100%", thickness=1, color=BORDER_COLOR),
        ]

    def _build_lines_table(self, cmd: dict) -> list:
        """Build the items table."""
        lignes = cmd.get("lignes", [])
        if not lignes:
            return [Paragraph("Aucun article", STYLE_BODY)]

        col_widths = [52 * mm, 14 * mm, 20 * mm, 18 * mm, 24 * mm]
        header = [
            Paragraph("<b>Désignation</b>", STYLE_BODY_BOLD),
            Paragraph("<b>Qté</b>", STYLE_BODY_BOLD),
            Paragraph("<b>Prix unitaire</b>", STYLE_CENTER),
            Paragraph("<b>TVA</b>", STYLE_CENTER),
            Paragraph("<b>Total</b>", STYLE_RIGHT),
        ]

        data = [header]
        for lc in lignes:
            nom = lc.get("produit_nom", lc.get("produit_id", "—"))
            qte = int(lc["quantite"])
            pu = float(lc["prix_unitaire"])
            tva = float(lc.get("taux_tva_applique", 0))
            total_ligne = pu * qte

            data.append([
                Paragraph(f"{nom}<br/>"
                          f"<font size='8' color='grey'>{lc.get('commentaire', '')}</font>"
                          if lc.get("commentaire") else nom,
                          STYLE_BODY),
                Paragraph(str(qte), STYLE_CENTER),
                Paragraph(f"{pu:,.0f} F", STYLE_CENTER),
                Paragraph(f"{tva:.0f}%", STYLE_CENTER),
                Paragraph(f"{total_ligne:,.0f} F", STYLE_RIGHT),
            ])

        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            # Rows
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            # Alternating row colors
            *[("BACKGROUND", (0, i), (-1, i), LIGHT_BG) for i in range(2, len(data), 2)],
            # Line above footer
            ("LINEABOVE", (0, 0), (-1, 0), 0.5, BORDER_COLOR),
            ("LINEBELOW", (0, -1), (-1, -1), 1, PRIMARY_COLOR),
        ]))

        return [table]

    def _build_totals(self, cmd: dict) -> list:
        """Build totals section."""
        total = float(cmd.get("total", 0))
        tva = float(cmd.get("montant_tva", 0))
        ht = total - tva

        data = [
            ["", Paragraph("<b>Total HT</b>", STYLE_BODY_BOLD),
             Paragraph(f"<b>{ht:,.0f} F</b>", STYLE_RIGHT)],
            ["", Paragraph("TVA", STYLE_BODY),
             Paragraph(f"{tva:,.0f} F", STYLE_RIGHT)],
            ["", Paragraph("<b>Total TTC</b>", STYLE_BODY_BOLD),
             Paragraph(f"<b>{total:,.0f} F</b>", STYLE_RIGHT)],
        ]

        table = Table(data, colWidths=[50 * mm, 40 * mm, 38 * mm])
        table.setStyle(TableStyle([
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LINEABOVE", (1, -1), (2, -1), 1, PRIMARY_COLOR),
        ]))

        return [table]

    def _build_payment_info(self, cmd: dict) -> list:
        """Build payment method and status section."""
        paiement = cmd.get("moyen_paiement", "—")
        statut = cmd.get("statut_paiement", "en_attente")

        paiement_map = {
            "cash": "Espèces",
            "tmoney": "TMoney",
            "flooz": "Flooz",
            "mixte": "Mixte",
        }
        statut_map = {
            "en_attente": "En attente",
            "paye": "Payé",
            "echoue": "Échoué",
            "rembourse": "Remboursé",
        }

        payment_text = (
            f"Moyen de paiement : {paiement_map.get(paiement, paiement)}<br/>"
            f"Statut : {statut_map.get(statut, statut)}"
        )
        if cmd.get("transaction_id"):
            payment_text += f"<br/>Transaction : {cmd['transaction_id']}"

        return [Paragraph(payment_text, STYLE_BODY)]

    def _build_footer(self, cmd: dict) -> list:
        """Build footer with mission and thanks."""
        mission = cmd.get("mission", "")
        elements = []

        if mission:
            elements.append(Spacer(1, 4 * mm))
            elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
            elements.append(Spacer(1, 4 * mm))
            elements.append(Paragraph(mission, STYLE_FOOTER))

        elements.append(Spacer(1, 6 * mm))
        elements.append(Paragraph(
            "Merci de votre confiance ! — ArtizBoard",
            STYLE_FOOTER,
        ))
        elements.append(Paragraph(
            f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            STYLE_SMALL,
        ))

        return elements

    # ── Thermal receipt (ESC/POS) ──

    def print_thermal(self, commande_id: str, printer_ip: str = "192.168.1.100",
                      printer_port: int = 9100) -> bool:
        """Print receipt to network thermal printer via ESC/POS."""
        cmd = self._fetch_commande(commande_id)

        try:
            printer = EscposNetwork(printer_ip, port=printer_port)
            printer.set(align="center", bold=True, double_height=True, double_width=True)
            printer.text(cmd.get("etablissement_nom", "ArtizBoard")[:32] + "\n")
            printer.set(align="center", bold=False, double_height=False, double_width=False, normal_textsize=True)
            printer.text(cmd.get("adresse", "")[:40] + "\n")
            printer.text(f"Tel: {cmd.get('telephone', '')}\n")

            printer.set(align="left")
            printer.text("-" * 32 + "\n")

            # Invoice info
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT numero_facture FROM factures WHERE commande_id = %s",
                (commande_id,),
            )
            facture = cur.fetchone()
            cur.close()

            numero = facture["numero_facture"] if facture else "N/A"
            date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
            printer.text(f"Facture: {numero}\n")
            printer.text(f"Date: {date_str}\n")

            ref = cmd.get("reference_client", "")
            if ref:
                printer.text(f"Table: {ref}\n")

            printer.text("-" * 32 + "\n")

            # Items
            printer.set(align="left")
            printer.text("Qté  Article                Total\n")
            printer.text("-" * 32 + "\n")

            for lc in cmd.get("lignes", []):
                nom = (lc.get("produit_nom", "") or "")[:22]
                qte = str(int(lc["quantite"]))
                total_ligne = float(lc["prix_unitaire"]) * int(lc["quantite"])
                line = f"{qte:>3}x {nom:<22} {total_ligne:,.0f}\n"
                printer.text(line)

            printer.text("-" * 32 + "\n")

            # Total
            total = float(cmd.get("total", 0))
            printer.set(align="right", bold=True, double_height=True)
            printer.text(f"TOTAL: {total:,.0f} F\n")
            printer.set(double_height=False, normal_textsize=True)

            # Payment
            paiement_map = {"cash": "Espèces", "tmoney": "TMoney", "flooz": "Flooz"}
            paiement = paiement_map.get(cmd.get("moyen_paiement", ""), "")
            if paiement:
                printer.set(align="center")
                printer.text(f"Paiement: {paiement}\n")

            # Footer
            printer.text("-" * 32 + "\n")
            printer.set(align="center", bold=False)
            mission = cmd.get("mission", "")[:60]
            if mission:
                printer.text(mission + "\n")
            printer.text("Merci de votre visite !\n")
            printer.ln(3)

            # Cut paper
            printer.cut()
            printer.close()

            # Mark as printed
            if facture:
                cur = self.conn.cursor()
                cur.execute(
                    "UPDATE factures SET imprimee = TRUE WHERE commande_id = %s",
                    (commande_id,),
                )
                self.conn.commit()
                cur.close()

            logger.info(f"Reçu imprimé: commande {commande_id} → {printer_ip}:{printer_port}")
            return True

        except Exception as e:
            logger.error(f"Échec impression: {e}")
            return False

    def get_receipt_text(self, commande_id: str) -> str:
        """Generate receipt as plain text (for preview or fallback)."""
        cmd = self._fetch_commande(commande_id)

        W = 32
        lines = []
        lines.append(cmd.get("etablissement_nom", "ArtizBoard")[:W].center(W))
        lines.append(cmd.get("adresse", "")[:W].center(W))
        lines.append(f"Tel: {cmd.get('telephone', '')}".center(W))
        lines.append("-" * W)

        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT numero_facture FROM factures WHERE commande_id = %s", (commande_id,))
        facture = cur.fetchone()
        cur.close()
        numero = facture["numero_facture"] if facture else "N/A"

        date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        lines.append(f"Facture: {numero}")
        lines.append(f"Date: {date_str}")
        ref = cmd.get("reference_client", "")
        if ref:
            lines.append(f"Table: {ref}")
        lines.append("-" * W)
        lines.append(f"{'Qté':>3}  {'Article':<20} {'Total':>6}")
        lines.append("-" * W)

        for lc in cmd.get("lignes", []):
            nom = (lc.get("produit_nom", "") or "")[:20]
            qte = int(lc["quantite"])
            total_ligne = float(lc["prix_unitaire"]) * qte
            lines.append(f"{qte:>3}x {nom:<20} {total_ligne:>6,.0f}")

        lines.append("-" * W)
        total = float(cmd.get("total", 0))
        lines.append(f"{'TOTAL:':>14} {total:>16,.0f} F")

        paiement_map = {"cash": "Espèces", "tmoney": "TMoney", "flooz": "Flooz"}
        paiement = paiement_map.get(cmd.get("moyen_paiement", ""), "")
        if paiement:
            lines.append(f"  Paiement: {paiement}")

        lines.append("-" * W)
        mission = cmd.get("mission", "")[:W]
        if mission:
            lines.append(mission.center(W))
        lines.append("Merci de votre visite !".center(W))

        return "\n".join(lines)


# ── Convenience function ──

def generate_invoice(conn: PgConnection, commande_id: str,
                     created_by: str = "") -> Tuple[str, Path, str]:
    """Quick invoice generation. Used by admin_app and staff_app."""
    gen = InvoiceGenerator(conn)
    return gen.generate(commande_id, created_by=created_by)
