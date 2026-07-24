"""Seed 10 theme presets for WordPress templates.

5 Restaurant-only + 5 Boutique/Restaurant.
Chaque preset est un jeu de couleurs + CSS moderne.
"""
import uuid
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

import psycopg2
from ArtizBoardCommon.config_loader import get_db_config

db = get_db_config()
conn = psycopg2.connect(host=db[0], port=db[1], dbname=db[2],
                        user=db[3], password=db[4], client_encoding="UTF8")
cur = conn.cursor()

cur.execute("SELECT id FROM etablissements WHERE deleted_at IS NULL LIMIT 1")
eid = cur.fetchone()
if not eid:
    print("Aucun etablissement — lancer seed_db.py d'abord")
    sys.exit(1)
eid = eid[0]

# Supprimer les anciens presets
cur.execute("DELETE FROM theme_config WHERE etablissement_id = %s", (eid,))
conn.commit()

PRESETS = [
    # === RESTAURANT ONLY ===
    {
        "theme_id": "resto-classico",
        "theme_name": "Classico Italiano",
        "type": "restaurant",
        "primary_color": "#8B0000",  # Rouge bordeaux
        "secondary_color": "#D4A017",  # Or italien
        "accent_color": "#2E7D32",     # Vert olive
        "surface_color": "#FFF8F0",    # Crème
        "background_color": "#FFFBF7",
        "font_heading": "Playfair Display",
        "font_body": "Lora",
        "hero_title": "Ristorante",
        "hero_subtitle": "Cuisine italienne authentique depuis 1985.",
        "custom_css": """
.hero { background: linear-gradient(135deg, var(--primary), #4A0000); }
.nav { border-bottom: 2px solid var(--secondary); }
.nav-brand { font-family: 'Playfair Display', serif; font-style: italic; }
.product-card { border-left: 3px solid var(--secondary); }
.btn-primary { text-transform: uppercase; letter-spacing: 2px; }
""",
    },
    {
        "theme_id": "resto-zen",
        "theme_name": "Zen Minimal",
        "type": "restaurant",
        "primary_color": "#1A1A2E",
        "secondary_color": "#E94560",
        "accent_color": "#0F3460",
        "surface_color": "#FAFAFA",
        "background_color": "#FFFFFF",
        "font_heading": "Inter",
        "font_body": "Inter",
        "hero_title": "Zen Table",
        "hero_subtitle": "Simplicité. Élégance. Saveur.",
        "custom_css": """
.hero { background: #1A1A2E; border-radius: 0 0 60px 60px; }
.product-card { border-radius: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.04); }
.product-price { font-size: 1.5rem; font-weight: 800; }
.qty-btn { border-radius: 50%; width: 36px; height: 36px; }
""",
    },
    {
        "theme_id": "resto-bistro",
        "theme_name": "Bistro Urbain",
        "type": "restaurant",
        "primary_color": "#FF6B35",
        "secondary_color": "#004E89",
        "accent_color": "#1A659E",
        "surface_color": "#F7F7F7",
        "background_color": "#FFFFFF",
        "font_heading": "Montserrat",
        "font_body": "Open Sans",
        "hero_title": "Le Bistro",
        "hero_subtitle": "Fast. Frais. Gourmand.",
        "custom_css": """
.hero { background: linear-gradient(45deg, #FF6B35, #FF8C42); }
.hero-title { font-size: 3rem; text-transform: uppercase; }
.product-card { border-bottom: 3px solid var(--primary); border-radius: 0; }
.nav-link.active { background: var(--primary); color: white; }
""",
    },
    {
        "theme_id": "resto-luxe",
        "theme_name": "Gastronomique",
        "type": "restaurant",
        "primary_color": "#1C110A",
        "secondary_color": "#C9A96E",
        "accent_color": "#8B6914",
        "surface_color": "#FDF8F0",
        "background_color": "#FFFDF9",
        "font_heading": "Cormorant Garamond",
        "font_body": "Cormorant Garamond",
        "hero_title": "L'Écrin",
        "hero_subtitle": "Gastronomie étoilée au cœur de la ville.",
        "custom_css": """
.hero { background: linear-gradient(rgba(28,17,10,0.8),rgba(28,17,10,0.9)), url('https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=1200'); background-size: cover; background-position: center; min-height: 80vh; }
.hero-title { font-size: 4rem; font-weight: 300; letter-spacing: 4px; }
.product-card { border: 1px solid var(--secondary); }
.section-title { font-weight: 300; letter-spacing: 3px; text-transform: uppercase; }
""",
    },
    {
        "theme_id": "resto-street",
        "theme_name": "Street Food",
        "type": "restaurant",
        "primary_color": "#E63946",
        "secondary_color": "#F4A261",
        "accent_color": "#2A9D8F",
        "surface_color": "#FFF3E0",
        "background_color": "#FFFAF5",
        "font_heading": "Bebas Neue",
        "font_body": "Nunito",
        "hero_title": "STREET EATS",
        "hero_subtitle": "Saveurs du monde dans votre assiette.",
        "custom_css": """
.hero { background: repeating-linear-gradient(45deg, #E63946, #E63946 20px, #C1121F 20px, #C1121F 40px); }
.hero-title { font-size: 5rem; text-shadow: 3px 3px 0 rgba(0,0,0,0.2); }
.product-card { background: white; border: 2px solid #111; box-shadow: 6px 6px 0 rgba(0,0,0,0.1); }
.btn-primary { border-radius: 0; text-transform: uppercase; font-weight: 900; }
""",
    },
    # === BOUTIQUE / RESTAURANT ===
    {
        "theme_id": "br-wine",
        "theme_name": "Cave & Dégustation",
        "type": "boutique_restaurant",
        "primary_color": "#722F37",
        "secondary_color": "#B68B40",
        "accent_color": "#2C1810",
        "surface_color": "#FAF5F0",
        "background_color": "#FFFCF8",
        "font_heading": "Playfair Display",
        "font_body": "Lato",
        "hero_title": "La Cave",
        "hero_subtitle": "Dégustation & Épicerie fine.",
        "custom_css": """
.hero { background: linear-gradient(135deg, #2C1810, #722F37); }
.nav { background: #2C1810; }
.nav-link, .nav-brand { color: #D4C5B2 !important; }
.nav-link.active { background: #722F37; }
.product-card { display: grid; grid-template-columns: 120px 1fr; gap: 0; padding: 0; }
.product-card img { width: 120px; height: 120px; object-fit: cover; }
""",
    },
    {
        "theme_id": "br-coffee",
        "theme_name": "Coffee Shop",
        "type": "boutique_restaurant",
        "primary_color": "#6F4E37",
        "secondary_color": "#D4A574",
        "accent_color": "#3E2723",
        "surface_color": "#FFF8F0",
        "background_color": "#FDF6EE",
        "font_heading": "Georgia",
        "font_body": "Source Sans Pro",
        "hero_title": "Morning Brew",
        "hero_subtitle": "Café torréfié maison & douceurs artisanales.",
        "custom_css": """
.hero { background: linear-gradient(rgba(0,0,0,0.3),rgba(0,0,0,0.5)), url('https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=1200'); background-size: cover; }
.hero-title { font-size: 2.5rem; }
.nav { box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
.product-card { background: #FFF; border-radius: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.btn-primary { border-radius: 30px; padding: 12px 28px; }
""",
    },
    {
        "theme_id": "br-bakery",
        "theme_name": "Boulangerie & Salon de thé",
        "type": "boutique_restaurant",
        "primary_color": "#D4A373",
        "secondary_color": "#FAEDCD",
        "accent_color": "#CCD5AE",
        "surface_color": "#FEFAE0",
        "background_color": "#FFFDF7",
        "font_heading": "Nunito",
        "font_body": "Nunito",
        "hero_title": "La Mie Dorée",
        "hero_subtitle": "Pains, viennoiseries & salon de thé.",
        "custom_css": """
.hero { background: linear-gradient(135deg, #FAEDCD, #FEFAE0, #CCD5AE); color: #5C4033; }
.hero-title { color: #5C4033; }
.hero-subtitle { color: #8B6914; }
.nav { background: #FFFDF7; border-bottom: 1px solid #FAEDCD; }
.product-card { background: #FFF; border-radius: 24px; }
.btn-primary { background: #D4A373; color: #FFF; border-radius: 24px; }
.btn-primary:hover { background: #C08B5C; }
""",
    },
    {
        "theme_id": "br-organic",
        "theme_name": "Marché Bio",
        "type": "boutique_restaurant",
        "primary_color": "#2D6A4F",
        "secondary_color": "#52B788",
        "accent_color": "#D8F3DC",
        "surface_color": "#F0FAF0",
        "background_color": "#F8FFF8",
        "font_heading": "Josefin Sans",
        "font_body": "Josefin Sans",
        "hero_title": "Terre & Saveurs",
        "hero_subtitle": "Produits locaux, cuisine de saison.",
        "custom_css": """
.hero { background: linear-gradient(135deg, #1B4332, #2D6A4F, #40916C); }
.product-card { border: 1px solid #D8F3DC; border-radius: 12px; }
.product-card:hover { border-color: #52B788; box-shadow: 0 4px 16px rgba(45,106,79,0.15); }
.product-price { color: #2D6A4F; }
.nav-link.active { background: #D8F3DC; color: #2D6A4F; }
.btn-primary { background: #2D6A4F; border-radius: 8px; }
.footer { background: #1B4332; color: #D8F3DC; }
""",
    },
    {
        "theme_id": "br-concept",
        "theme_name": "Concept Store",
        "type": "boutique_restaurant",
        "primary_color": "#000000",
        "secondary_color": "#FFD700",
        "accent_color": "#333333",
        "surface_color": "#F5F5F5",
        "background_color": "#FFFFFF",
        "font_heading": "Inter",
        "font_body": "Inter",
        "hero_title": "THE STORE",
        "hero_subtitle": "Manger. Boire. Acheter.",
        "custom_css": """
.hero { background: #000; border-bottom: 4px solid var(--secondary); }
.hero-title { font-size: 5rem; font-weight: 900; letter-spacing: -2px; }
.nav { background: #000; border-bottom: 1px solid #333; }
.nav-link, .nav-brand { color: #AAA !important; }
.nav-link.active { background: #333; color: #FFF !important; }
.nav-brand { font-weight: 900; letter-spacing: -1px; }
.product-card { border: 1px solid #EEE; transition: all 0.3s; }
.product-card:hover { border-color: #000; transform: translateY(-2px); }
.btn-primary { background: #000; color: #FFF; border-radius: 0; font-weight: 900; text-transform: uppercase; letter-spacing: 1px; }
.btn-primary:hover { background: #333; }
.section-title { font-weight: 900; letter-spacing: -1px; }
""",
    },
]

# Insérer tous les presets
for p in PRESETS:
    cur.execute("""
        INSERT INTO theme_config (id, etablissement_id, theme_id, theme_name,
            primary_color, secondary_color, accent_color, surface_color, background_color,
            font_heading, font_body, hero_title, hero_subtitle, custom_css, est_actif)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        str(uuid.uuid4()), eid, p["theme_id"], p["theme_name"],
        p["primary_color"], p["secondary_color"], p["accent_color"],
        p["surface_color"], p["background_color"],
        p["font_heading"], p["font_body"],
        p["hero_title"], p["hero_subtitle"],
        p["custom_css"], True
    ))

conn.commit()

# Vérifier
cur.execute("SELECT theme_id, theme_name FROM theme_config WHERE deleted_at IS NULL ORDER BY theme_id")
rows = cur.fetchall()
print(f"{len(rows)} presets dans theme_config:")
for r in rows:
    print(f"  {r[0]:20s} {r[1]}")

cur.close()
conn.close()
print("\nDone. Lance python sync_service.py pour pousser vers Supabase.")
