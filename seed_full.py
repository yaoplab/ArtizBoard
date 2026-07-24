"""Create missing tables and seed data."""
import sys, uuid, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import psycopg2, psycopg2.extras
from datetime import datetime, timedelta, timezone
from ArtizBoardCommon.config_loader import get_db_config

db = get_db_config()
conn = psycopg2.connect(host=db[0], port=db[1], dbname=db[2],
                        user=db[3], password=db[4], client_encoding="UTF8")
conn.autocommit = False
cur = conn.cursor()

# ═══════════ CREATE MISSING TABLES ═══════════
try:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id UUID PRIMARY KEY,
            etablissement_id UUID NOT NULL REFERENCES etablissements(id),
            titre VARCHAR(255) NOT NULL,
            slug VARCHAR(255) NOT NULL,
            contenu TEXT,
            ordre INTEGER DEFAULT 0,
            created_by UUID REFERENCES utilisateurs(id),
            updated_by UUID REFERENCES utilisateurs(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
            sync_status VARCHAR(20) DEFAULT 'local'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS theme_config (
            id UUID PRIMARY KEY,
            etablissement_id UUID NOT NULL REFERENCES etablissements(id),
            theme_id VARCHAR(50),
            primary_color VARCHAR(7),
            secondary_color VARCHAR(7),
            accent_color VARCHAR(7),
            surface_color VARCHAR(7),
            font_heading VARCHAR(100),
            font_body VARCHAR(100),
            hero_title VARCHAR(255),
            hero_subtitle TEXT,
            hero_button_text VARCHAR(100),
            hero_image_url TEXT,
            seo_title_template VARCHAR(255),
            seo_description TEXT,
            facebook_url VARCHAR(255),
            instagram_url VARCHAR(255),
            whatsapp_number VARCHAR(50),
            footer_text TEXT,
            custom_css TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS theme_presets (
            id UUID PRIMARY KEY,
            theme_id VARCHAR(50) UNIQUE NOT NULL,
            theme_name VARCHAR(100) NOT NULL,
            primary_color VARCHAR(7),
            secondary_color VARCHAR(7),
            accent_color VARCHAR(7),
            surface_color VARCHAR(7),
            font_heading VARCHAR(100),
            hero_title VARCHAR(255),
            hero_subtitle TEXT,
            hero_button_text VARCHAR(100),
            hero_image_url TEXT,
            custom_css TEXT
        )
    """)

    # Add version to theme_config
    try:
        cur.execute("ALTER TABLE theme_config ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1")
    except: pass

    conn.commit()
    print("Tables created.")
except Exception as e:
    conn.rollback()
    print(f"Tables: {e}")

# Get IDs
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("SELECT id FROM etablissements LIMIT 1")
EID = dict(cur.fetchone())["id"]
cur.execute("SELECT id FROM utilisateurs WHERE email='admin@larepublique.tg'")
AID = dict(cur.fetchone())["id"]

# ═══════════ PAGES ═══════════
print("Seed pages...")
cur.execute("SELECT count(*) as n FROM pages WHERE etablissement_id=%s", (EID,))
if cur.fetchone()["n"] == 0:
    for titre, slug, contenu, ordre in [
        ("Notre Histoire", "notre-histoire",
         "Le Restaurant La Republique a ete fonde en 2010 par le Chef Patrice Akakpo.\n\n"
         "Apres 15 ans de cuisine en Afrique de l'Ouest, il a cree un lieu ou la tradition "
         "rencontre la modernite.\n\n**Notre philosophie :** produits frais du marche local, "
         "recettes transmises, touche contemporaine.", 1),
        ("Notre Carte", "notre-carte",
         "Decouvrez notre menu qui change au fil des saisons.\n\n"
         "* **Entrees** : salades, beignets, samoussas\n"
         "* **Plats** : riz au gras, sauce arachide, poulet braise\n"
         "* **Desserts** : creme caramel, salade de fruits\n"
         "* **Boissons** : bissap, gingembre, cocktails", 2),
        ("Nous Contacter", "nous-contacter",
         "**Restaurant La Republique**\n\n123 Avenue de la Republique, Lome\n\n"
         "Tel: +228 90 00 00 01 | Email: contact@larepublique.tg\n\n"
         "**Horaires :** Lun-Jeu 11h-22h, Ven-Sam 11h-23h30, Dim 12h-21h", 3),
    ]:
        cur.execute("""INSERT INTO pages (id, etablissement_id, titre, slug, contenu, ordre, created_by, updated_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (str(uuid.uuid4()), EID, titre, slug, contenu, ordre, AID, AID))
    conn.commit()
    print("  3 pages (Notre Histoire, Carte, Contact)")
else:
    print("  Pages already exist")

# ═══════════ THEME CONFIG ═══════════
print("Seed theme_config...")
cur.execute("SELECT count(*) as n FROM theme_config WHERE etablissement_id=%s", (EID,))
if cur.fetchone()["n"] == 0:
    cur.execute("""INSERT INTO theme_config (id, etablissement_id, theme_id,
        primary_color, secondary_color, accent_color, surface_color,
        font_heading, font_body, hero_title, hero_subtitle, hero_button_text,
        hero_image_url, seo_title_template, seo_description,
        facebook_url, instagram_url, whatsapp_number, footer_text, custom_css, version)
        VALUES (%s,%s,%s, %s,%s,%s,%s, %s,%s, %s,%s,%s, %s, %s,%s, %s,%s,%s, %s, %s, %s)""",
        (str(uuid.uuid4()), EID, "restaurant-warm",
         "#C62828", "#FF8F00", "#2E7D32", "#FFF8E1",
         "Playfair Display", "Open Sans",
         "Restaurant La Republique", "Cuisine africaine a Lome", "Voir la carte",
         "/uploads/hero.jpg", "{page_title} — La Republique", "Restaurant africain contemporain a Lome",
         "https://fb.com/LaRepubliqueLome", "https://insta.com/larepublique", "+22890000001",
         "© 2026 Restaurant La Republique", "body{font-family:Open Sans}h1{font-family:Playfair Display}", 1))
    conn.commit()
    print("  Theme config: restaurant-warm")
else:
    print("  Theme config exists")

# ═══════════ THEME PRESETS ═══════════
print("Seed theme presets...")
presets = [
    ("restaurant-warm", "Restaurant Chaleureux", "#C62828", "#FF8F00", "#2E7D32", "#FFF8E1", "Playfair Display",
     "La Republique", "Cuisine africaine contemporaine", "Voir la carte", "/uploads/hero1.jpg",
     ".hero{background:linear-gradient(135deg,#C62828,#FF8F00)}"),
    ("restaurant-dark", "Restaurant Elegant", "#1A1A2E", "#E94560", "#16213E", "#F5F5F5", "Playfair Display",
     "La Republique", "Saveurs d'exception", "Decouvrir", "/uploads/hero2.jpg",
     ".hero{background:linear-gradient(180deg,#1A1A2E,#16213E)}body{color:#333}"),
    ("restaurant-green", "Restaurant Nature", "#2E7D32", "#81C784", "#1B5E20", "#F1F8E9", "Merriweather",
     "La Republique", "Du champ a l'assiette", "Notre carte", "/uploads/hero3.jpg",
     ".hero{background:linear-gradient(135deg,#2E7D32,#81C784)}"),
    ("boutique-elegance", "Boutique Elegance", "#3F51B5", "#FF4081", "#303F9F", "#FFFFFF", "Montserrat",
     "La Republique Boutique", "Produits d'exception", "Acheter", "/uploads/hero4.jpg",
     ".hero{background:linear-gradient(90deg,#3F51B5,#FF4081)}"),
    ("boutique-minimal", "Boutique Minimaliste", "#212121", "#F5F5F5", "#757575", "#FFFFFF", "Inter",
     "La Republique", "Simplicite et qualite", "Explorer", "/uploads/hero5.jpg",
     "body{background:#fafafa}.hero{background:#212121}"),
    ("boutique-nature", "Boutique Artisanale", "#5D4037", "#8D6E63", "#3E2723", "#EFEBE9", "Lora",
     "La Republique", "Artisanat authentique", "Decouvrir", "/uploads/hero6.jpg",
     ".hero{background:linear-gradient(180deg,#5D4037,#8D6E63)}"),
    ("hybrid-market", "Marche Gourmand", "#E65100", "#1565C0", "#2E7D32", "#FFF3E0", "Roboto Slab",
     "La Republique", "Restaurant & Boutique", "Commander", "/uploads/hero7.jpg",
     ".hero{background:linear-gradient(135deg,#E65100,#1565C0)}"),
    ("hybrid-cafe", "Cafe Librairie", "#4E342E", "#FFB300", "#3E2723", "#FFF8E1", "Georgia",
     "La Republique", "Cafe, lectures & saveurs", "Reserver", "/uploads/hero8.jpg",
     ".hero{background:linear-gradient(180deg,#4E342E,#3E2723)}"),
    ("modern-slate", "Ardoise Moderne", "#37474F", "#546E7A", "#263238", "#ECEFF1", "Inter",
     "La Republique", "Modernite et tradition", "Explorer", "/uploads/hero9.jpg",
     ".hero{background:#37474F}body{background:#ECEFF1}"),
    ("ocean-breeze", "Brise Marine", "#0277BD", "#00BCD4", "#01579B", "#E1F5FE", "Nunito",
     "La Republique", "Fraicheur de l'ocean", "Decouvrir", "/uploads/hero10.jpg",
     ".hero{background:linear-gradient(135deg,#0277BD,#00BCD4)}"),
]

cur.execute("SELECT count(*) as n FROM theme_presets")
if cur.fetchone()["n"] == 0:
    for tid, tn, pc, sc, ac, sur, font, ht, hs, hb, hi, css in presets:
        cur.execute("""INSERT INTO theme_presets (id, theme_id, theme_name,
            primary_color, secondary_color, accent_color, surface_color,
            font_heading, hero_title, hero_subtitle, hero_button_text, hero_image_url, custom_css)
            VALUES (%s,%s,%s, %s,%s,%s,%s, %s, %s,%s,%s,%s,%s)""",
            (str(uuid.uuid4()), tid, tn, pc, sc, ac, sur, font, ht, hs, hb, hi, css))
    conn.commit()
    print(f"  10 theme presets (5 resto + 5 boutique)")
else:
    cur.execute("SELECT count(*) as n FROM theme_presets")
    print(f"  {cur.fetchone()['n']} presets already exist")

cur.close()
conn.close()
print("\nDone. Relance: python -m apps.admin")
