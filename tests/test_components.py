"""Tests for ArtizBoardCommon components (instantiation, no rendering)."""
import sys, pytest
sys.path.insert(0, r'C:\projet')

from ArtizBoardCommon import ds
from ArtizBoardCommon.components import (
    button, card, textfield, kpi_card, chip, dialog, confirm_dialog,
    snackbar, badge, banner, section_header, headline, title, body, label,
    caption, spacer, divider, container, row, column, empty_state,
    ButtonVariant, CardVariant, Severity,
)


class TestTypography:
    """Typography helpers."""

    def test_headline(self):
        h = headline("Test", size="medium")
        assert h.value == "Test"
        assert h.style.size == ds.typo.headline_medium.size

    def test_title(self):
        t = title("Section", size="medium")
        assert t.value == "Section"

    def test_body(self):
        b = body("Body text", size="small")
        assert b.value == "Body text"

    def test_label(self):
        l = label("Label")
        assert l is not None

    def test_caption(self):
        c = caption("Small text")
        assert c.value == "Small text"


class TestLayoutHelpers:
    """Layout helpers."""

    def test_spacer(self):
        s = spacer()
        assert isinstance(s.height, int)

    def test_divider(self):
        d = divider()
        assert d.height >= 1

    def test_container(self):
        c = container(None)
        assert c.expand is False

    def test_row(self):
        r = row([])
        assert len(r.controls) == 0

    def test_column(self):
        c = column([])
        assert len(c.controls) == 0


class TestComponents:
    """Component instantiation tests."""

    def test_button_filled(self):
        btn = button("Valider", variant=ButtonVariant.FILLED)
        assert btn is not None

    def test_button_tonal(self):
        btn = button("Suivant", variant=ButtonVariant.TONAL)
        assert btn is not None

    def test_button_outlined(self):
        btn = button("Annuler", variant=ButtonVariant.OUTLINED)
        assert btn is not None

    def test_button_text(self):
        btn = button("Lié", variant=ButtonVariant.TEXT)
        assert btn is not None

    def test_button_elevated(self):
        btn = button("Haut", variant=ButtonVariant.ELEVATED)
        assert btn is not None

    def test_button_with_icon(self):
        from flet import Icons
        btn = button("Save", icon=Icons.SAVE)
        assert btn is not None

    def test_textfield(self):
        tf = textfield(label="Email", hint="nom@exemple.com")
        assert tf.label == "Email"

    def test_textfield_with_icon(self):
        tf = textfield(label="Recherche", prefix_icon="search")
        assert tf is not None

    def test_card_elevated(self):
        c = card("Titre", variant=CardVariant.ELEVATED)
        assert c is not None

    def test_card_filled(self):
        c = card("Titre", variant=CardVariant.FILLED)
        assert c is not None

    def test_kpi_card(self):
        k = kpi_card("500 000 F", "CA du jour", icon="trending_up")
        assert k is not None

    def test_chip(self):
        c = chip("Filtrer")
        assert c is not None

    def test_section_header(self):
        s = section_header("Titre de section")
        assert s is not None

    def test_section_header_with_action(self):
        from flet import Icons
        s = section_header("Titre", action=button("+", variant=ButtonVariant.TEXT))
        assert s is not None


class TestDialogs:
    """Dialog component tests."""

    def test_dialog(self):
        from flet import AlertDialog
        d = dialog("Titre", content="Contenu")
        assert isinstance(d, AlertDialog)

    def test_confirm_dialog(self):
        from flet import AlertDialog
        d = confirm_dialog("Supprimer ?", "Etes-vous sûr ?",
                           on_confirm=lambda: None)
        assert isinstance(d, AlertDialog)


class TestSnackbar:
    """Snackbar tests."""

    def test_snackbar_info(self):
        s = snackbar("Info")
        assert s is not None

    def test_snackbar_success(self):
        s = snackbar("OK", severity=Severity.SUCCESS)
        assert s is not None

    def test_snackbar_error(self):
        s = snackbar("Erreur", severity=Severity.ERROR)
        assert s is not None

    def test_snackbar_warning(self):
        s = snackbar("Attention", severity=Severity.WARNING)
        assert s is not None


class TestMisc:
    """Miscellaneous components."""

    def test_badge(self):
        b = badge("3", severity=Severity.ERROR)
        assert b is not None

    def test_banner(self):
        b = banner("Message", severity=Severity.SUCCESS)
        assert b is not None

    def test_empty_state(self):
        from flet import Icons
        e = empty_state(icon=Icons.INBOX, title="Vide")
        assert e is not None
