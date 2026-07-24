"""Seed 3 high-quality theme presets with distinct layouts.

Replaces the 10 color-only presets from seed_themes.py.
Each preset uses aggressive custom_css to completely transform the layout.
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

# Supprimer TOUS les presets (v1 et v2)
cur.execute("DELETE FROM theme_config WHERE etablissement_id = %s", (eid,))
conn.commit()

# ============================================================
# TEMPLATE 1: Fine Dining (resto-luxe)
# ============================================================
FINE_DINING_CSS = """
/* === FINE DINING — Full Override === */
:root {
  --primary: #C9A96E;
  --primary-dark: #8B6914;
  --secondary: #1C110A;
  --accent: #C9A96E;
  --surface: #FDF8F0;
  --background: #FFFDF9;
  --text-strong: #1C110A;
  --text-soft: #5C4033;
  --outline-variant: #D4C5B2;
  --font: 'Cormorant Garamond', 'Playfair Display', Georgia, serif;
  --fs-display: 3.5rem;
  --fs-headline: 2rem;
  --fs-title: 1.5rem;
  --fs-body: 1.05rem;
}

/* ---- Body & Reset ---- */
body { background: var(--background); color: var(--text-strong); }
.container { max-width: 1040px; }

/* ---- Navigation: Transparent & Elegant ---- */
.nav {
  background: rgba(253,248,240,0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--primary);
}
.nav-inner { max-width: 1040px; }
.nav-brand {
  font-family: var(--font);
  font-size: 1.8rem;
  font-weight: 300;
  letter-spacing: 3px;
  color: var(--primary-dark);
  text-transform: uppercase;
}
.nav-link {
  font-family: var(--font);
  font-size: 0.85rem;
  font-weight: 400;
  text-transform: uppercase;
  letter-spacing: 2px;
  border-radius: 0;
}
.nav-link:hover { color: var(--primary); background: transparent; }
.nav-link.active { color: var(--primary); background: transparent; border-bottom: 2px solid var(--primary); }

/* ---- Hero: Fullscreen Dark Overlay ---- */
.hero {
  min-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  background: linear-gradient(rgba(28,17,10,0.65), rgba(28,17,10,0.92)),
    url('https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=1400&q=80');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  color: #FDF8F0;
  padding: 0;
}
.hero-title {
  font-size: 5.5rem;
  font-weight: 300;
  letter-spacing: 8px;
  text-transform: uppercase;
  font-family: var(--font);
  margin-bottom: 1.5rem;
  line-height: 1.1;
}
.hero-subtitle {
  font-size: 1.35rem;
  font-weight: 300;
  letter-spacing: 3px;
  opacity: 0.85;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}
.hero .btn {
  background: transparent;
  border: 2px solid var(--primary);
  color: var(--primary);
  font-family: var(--font);
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 4px;
  padding: 16px 48px;
  border-radius: 0;
  margin-top: 3rem;
  transition: all 0.4s ease;
}
.hero .btn:hover {
  background: var(--primary);
  color: #1C110A;
}

/* ---- Section Titles: Elegant with Diamond Accent ---- */
.section-title {
  font-size: 2.2rem;
  font-weight: 300;
  letter-spacing: 4px;
  text-transform: uppercase;
  text-align: center;
  color: var(--primary-dark);
  margin-bottom: 3rem;
  position: relative;
  padding-bottom: 1.2rem;
}
.section-title::after {
  content: '\u25C6';
  display: block;
  font-size: 0.5rem;
  color: var(--primary);
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  letter-spacing: 0;
}

/* ---- Category List: Centered Pill Row ---- */
.cat-list {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 2rem;
  justify-content: center;
}
.cat-item {
  border: none;
  padding: 2.5rem 2rem 1.5rem;
  text-align: center;
  flex-direction: column;
  gap: 0.5rem;
  border-bottom: 2px solid transparent;
  background: transparent;
  transition: all 0.4s ease;
  cursor: pointer;
}
.cat-item:hover {
  border-bottom-color: var(--primary);
  background: transparent;
}
.cat-item-name {
  font-family: var(--font);
  font-size: 1.4rem;
  font-weight: 300;
  letter-spacing: 2px;
  color: var(--text-strong);
}
.cat-item-count {
  font-family: var(--font);
  font-size: 0.8rem;
  color: var(--primary);
  background: transparent;
  text-transform: uppercase;
  letter-spacing: 2px;
}

/* ---- Product Cards: Horizontal, Large Image, Elegant ---- */
.product-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.product-card {
  display: flex;
  align-items: stretch;
  gap: 0;
  padding: 0;
  background: #FFFFFF;
  border: none;
  border-radius: 0;
  overflow: hidden;
  min-height: 200px;
  transition: all 0.5s cubic-bezier(0.25,0.46,0.45,0.94);
  animation: fd-fade-in 0.6s ease both;
}
.product-card:nth-child(1) { animation-delay: 0.05s; }
.product-card:nth-child(2) { animation-delay: 0.10s; }
.product-card:nth-child(3) { animation-delay: 0.15s; }
.product-card:nth-child(4) { animation-delay: 0.20s; }
.product-card:nth-child(5) { animation-delay: 0.25s; }
.product-card:nth-child(6) { animation-delay: 0.30s; }
.product-card:nth-child(7) { animation-delay: 0.35s; }
.product-card:nth-child(8) { animation-delay: 0.40s; }
@keyframes fd-fade-in {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.product-card:hover {
  box-shadow: 0 12px 48px rgba(28,17,10,0.12);
  transform: translateY(-2px);
}
.product-card.in-cart {
  background: #FFFAF2;
  border-left: 4px solid var(--primary);
}
.product-image {
  width: 320px;
  height: 200px;
  border-radius: 0;
  object-fit: cover;
  flex-shrink: 0;
}
.product-info {
  padding: 2rem 2.5rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1;
}
.product-name {
  font-size: 1.4rem;
  font-weight: 400;
  letter-spacing: 1px;
  font-family: var(--font);
  margin-bottom: 0.5rem;
  color: var(--text-strong);
}
.product-desc {
  font-size: 0.95rem;
  color: var(--text-soft);
  font-style: italic;
  font-family: var(--font);
  line-height: 1.7;
  max-width: 500px;
}
.product-price {
  font-size: 1.6rem;
  font-weight: 300;
  color: var(--primary-dark);
  letter-spacing: 2px;
  font-family: var(--font);
  margin-top: 0.75rem;
}
.product-actions {
  padding: 2rem 2.5rem;
  display: flex;
  align-items: center;
  gap: 1.2rem;
  background: #FCF9F4;
  flex-shrink: 0;
}
.qty-btn {
  width: 38px;
  height: 38px;
  border: 1px solid var(--primary);
  color: var(--primary);
  background: transparent;
  font-family: var(--font);
  font-size: 1.2rem;
  border-radius: 50%;
  transition: all 0.3s ease;
}
.qty-btn:hover {
  background: var(--primary);
  color: #FFF;
}
.qty-value {
  font-family: var(--font);
  font-size: 1.1rem;
  font-weight: 400;
  color: var(--text-strong);
}

/* ---- Buttons ---- */
.btn-primary {
  background: var(--primary);
  color: var(--primary-dark);
  font-family: var(--font);
  text-transform: uppercase;
  letter-spacing: 3px;
  border-radius: 0;
  padding: 14px 36px;
}
.btn-primary:hover { background: #D4B87A; }
.btn-outline {
  border-color: var(--primary);
  color: var(--primary-dark);
  font-family: var(--font);
  letter-spacing: 2px;
  border-radius: 0;
}
.btn-outline:hover { background: var(--primary); color: #FFF; border-color: var(--primary); }

/* ---- Footer: Dark & Elegant ---- */
.footer {
  background: #1C110A;
  color: #C9A96E;
  border: none;
  font-family: var(--font);
  letter-spacing: 1.5px;
  padding: 3rem var(--space-md);
}
.footer a { color: var(--primary); }

/* ---- FAQ ---- */
.faq-item {
  background: #FFF;
  border-left: 3px solid var(--primary);
  border-radius: 0;
  padding: var(--space-lg);
}
.faq-question { font-family: var(--font); font-size: 1.1rem; letter-spacing: 1px; }

/* ---- Contact ---- */
.contact-card { background: #FFF; border: 1px solid var(--outline-variant); border-radius: 0; }

/* ---- Cart Drawer ---- */
.drawer { background: #FFFDF9; }
.drawer-header { border-bottom: 1px solid var(--primary); background: var(--surface); }
.drawer-body { background: #FFFDF9; }

/* ---- Page Tabs ---- */
.page-tab { font-family: var(--font); text-transform: uppercase; letter-spacing: 2px; }

/* ---- Responsive ---- */
@media(max-width:900px) {
  .hero { min-height: 60vh; background-attachment: scroll; }
  .hero-title { font-size: 3rem; letter-spacing: 4px; }
  .hero-subtitle { font-size: 1.05rem; }
  .product-card { flex-direction: column; }
  .product-image { width: 100%; height: 220px; }
  .product-actions { padding: 1rem 2rem; justify-content: flex-end; }
  .product-info { padding: 1.5rem; }
  .cat-list { gap: 0.5rem; }
  .cat-item { padding: 1.25rem 1rem; }
}
@media(max-width:600px) {
  .hero-title { font-size: 2.2rem; letter-spacing: 2px; }
  .product-image { height: 160px; }
  .section-title { font-size: 1.5rem; letter-spacing: 2px; }
}
"""

# ============================================================
# TEMPLATE 2: Street Food (resto-street)
# ============================================================
STREET_FOOD_CSS = """
/* === STREET FOOD — Full Override === */
:root {
  --primary: #E63946;
  --primary-dark: #C1121F;
  --secondary: #FFD700;
  --accent: #FFD700;
  --surface: #FFFFFF;
  --background: #F9F9F9;
  --text-strong: #111111;
  --text-soft: #444444;
  --outline-variant: #DDDDDD;
  --font: 'Bebas Neue', 'Anton', Impact, sans-serif;
  --fs-display: 4rem;
  --fs-headline: 2.5rem;
  --fs-title: 1.5rem;
  --fs-body: 1rem;
  --font-body: 'Nunito', 'Segoe UI', sans-serif;
}

/* ---- Body ---- */
body {
  background: var(--background);
  font-family: var(--font-body);
  color: var(--text-strong);
}

/* ---- Navigation: Black Bar ---- */
.nav {
  background: #111111;
  border-bottom: 3px solid var(--secondary);
  padding: 0;
}
.nav-inner { max-width: 1200px; }
.nav-brand {
  font-family: var(--font);
  font-size: 2rem;
  letter-spacing: 1.5px;
  color: var(--secondary) !important;
  text-transform: uppercase;
}
.nav-brand img { border-radius: 4px; }
.nav-link {
  color: #BBB !important;
  font-family: var(--font-body);
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 1px;
  border-radius: 8px;
  padding: 8px 16px;
}
.nav-link:hover, .nav-link.active {
  background: var(--primary);
  color: #FFF !important;
}
.nav-cart {
  background: var(--secondary);
  color: #111 !important;
  border-radius: 8px;
  font-weight: 900;
  padding: 8px 16px;
}
.cart-badge {
  background: var(--primary);
  color: #FFF;
  font-family: var(--font-body);
  font-weight: 900;
  border-radius: 50%;
  min-width: 22px;
  min-height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
}

/* ---- Hero: Diagonal Geometric Pattern ---- */
.hero {
  background:
    repeating-linear-gradient(45deg, #111111, #111111 10px, #1a1a1a 10px, #1a1a1a 20px);
  border-bottom: 6px solid var(--primary);
  padding: 5rem 1.5rem;
  text-align: center;
}
.hero-title {
  font-family: var(--font);
  font-size: 7rem;
  font-weight: 900;
  text-shadow: 5px 5px 0 var(--primary);
  letter-spacing: 3px;
  line-height: 0.9;
  color: var(--secondary);
  text-transform: uppercase;
  margin-bottom: 1rem;
}
.hero-subtitle {
  font-family: var(--font-body);
  font-size: 1.3rem;
  font-weight: 700;
  color: #FFFFFF;
  max-width: 600px;
}
.hero .btn {
  background: var(--primary);
  border: 3px solid #FFFFFF;
  font-family: var(--font);
  font-size: 1.6rem;
  letter-spacing: 2px;
  border-radius: 14px;
  padding: 16px 48px;
  color: #FFF;
  box-shadow: 0 6px 0 #C1121F;
  text-transform: uppercase;
  transition: all 0.1s ease;
}
.hero .btn:hover {
  transform: translateY(2px);
  box-shadow: 0 3px 0 #C1121F;
}
.hero .btn:active {
  transform: translateY(4px);
  box-shadow: 0 1px 0 #C1121F;
}

/* ---- Section Titles: Bold Left Border ---- */
.section-title {
  font-family: var(--font);
  font-size: 2.5rem;
  letter-spacing: 1.5px;
  text-align: left;
  color: #111;
  border-left: 6px solid var(--secondary);
  padding-left: 1rem;
  margin-bottom: 1.5rem;
}

/* ---- Container ---- */
.container { max-width: 1200px; }

/* ---- Category List: Bold Cards ---- */
.cat-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
}
.cat-item {
  background: #FFF;
  margin-bottom: 0;
  border-radius: 14px;
  border: 3px solid #E0E0E0;
  border-left: 6px solid var(--primary);
  padding: 1.25rem 1.5rem;
  transition: all 0.15s ease;
  cursor: pointer;
}
.cat-item:hover {
  border-color: #111;
  background: #FFFDE7;
  transform: translateY(-2px);
  box-shadow: 0 6px 0 rgba(0,0,0,0.08);
}
.cat-item-name {
  font-family: var(--font);
  font-size: 1.4rem;
  letter-spacing: 1px;
}
.cat-item-count {
  background: #F5F5F5;
  color: #666;
  font-family: var(--font-body);
  font-weight: 700;
  border-radius: 8px;
  padding: 4px 12px;
  font-size: 0.75rem;
  text-transform: uppercase;
}

/* ---- Product Grid: 4 Columns ---- */
.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}
.product-card {
  display: flex;
  flex-direction: column;
  padding: 0;
  gap: 0;
  background: #FFFFFF;
  border-radius: 18px;
  border: 3px solid #111111;
  overflow: hidden;
  box-shadow: 8px 8px 0 rgba(0,0,0,0.1);
  transition: all 0.15s cubic-bezier(0.34,1.56,0.64,1);
  cursor: pointer;
}
.product-card:hover {
  transform: translate(-3px, -3px);
  box-shadow: 14px 14px 0 rgba(230,57,70,0.3);
  border-color: var(--primary);
}
.product-card.in-cart {
  border-color: var(--secondary);
  background: #FFFDE7;
  box-shadow: 8px 8px 0 rgba(255,215,0,0.3);
}
.product-image {
  width: 100%;
  height: 200px;
  border-radius: 0;
  object-fit: cover;
  border-bottom: 3px solid #111;
}
.product-info {
  padding: 1.25rem;
  flex: 1;
}
.product-name {
  font-family: var(--font);
  font-size: 1.4rem;
  letter-spacing: 0.5px;
  line-height: 1.1;
}
.product-desc {
  display: none;
}
.product-price {
  font-family: var(--font-body);
  font-size: 1.5rem;
  font-weight: 900;
  color: var(--primary);
  margin-top: 0.25rem;
}
.product-actions {
  padding: 0 1.25rem 1.25rem;
  justify-content: flex-start;
  gap: 0.75rem;
}
.qty-btn {
  width: 36px;
  height: 36px;
  border: 2px solid #111;
  border-radius: 10px;
  font-weight: 900;
  color: #111;
  font-size: 1.1rem;
  background: #FFF;
  transition: all 0.15s;
}
.qty-btn:hover {
  background: #111;
  color: #FFF;
}
.qty-value {
  font-family: var(--font-body);
  font-weight: 900;
  font-size: 1.1rem;
  color: #111;
}

/* ---- Buttons ---- */
.btn-primary {
  background: var(--primary);
  color: #FFF;
  border-radius: 14px;
  font-family: var(--font);
  letter-spacing: 1.5px;
  font-size: 1rem;
  box-shadow: 0 5px 0 #C1121F;
  transition: all 0.1s;
  padding: 14px 32px;
}
.btn-primary:hover { transform: translateY(2px); box-shadow: 0 2px 0 #C1121F; }
.btn-primary:active { transform: translateY(4px); box-shadow: none; }
.btn-outline {
  border: 2px solid #111;
  border-radius: 10px;
  font-family: var(--font-body);
  font-weight: 700;
  color: #111;
  padding: 10px 20px;
}
.btn-outline:hover { background: #111; color: #FFF; }

/* ---- Floating Cart Button ---- */
#cartBtn {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 150;
  background: var(--secondary);
  color: #111 !important;
  width: 68px;
  height: 68px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 28px rgba(0,0,0,0.30);
  font-size: 2rem;
  border: 3px solid #111;
  transition: transform 0.15s;
}
#cartBtn:hover { transform: scale(1.1); }
#cartBtn .cart-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 26px;
  height: 26px;
}

/* ---- Footer ---- */
.footer {
  background: #111111;
  color: var(--secondary);
  border-top: 4px solid var(--primary);
  font-family: var(--font-body);
  font-weight: 700;
  padding: 2.5rem var(--space-md);
}

/* ---- Cart Drawer ---- */
.drawer { background: #FFF; border-left: 3px solid #111; }
.drawer-header { background: #111; color: var(--secondary); border-bottom: 3px solid var(--primary); }
.drawer-header h2 { font-family: var(--font); letter-spacing: 1px; }
.drawer-header .btn-icon { color: var(--secondary); }

/* ---- FAQ ---- */
.faq-item {
  background: #FFF;
  border-left: 5px solid var(--primary);
  border-radius: 10px;
}
.faq-question { font-family: var(--font-body); font-weight: 800; }

/* ---- Page Tabs ---- */
.page-tab {
  font-family: var(--font);
  letter-spacing: 1px;
  font-size: 1rem;
}
.page-tab.active { border-bottom: 3px solid var(--primary); }

/* ---- Search Input ---- */
#prodSearch {
  border: 3px solid #111 !important;
  border-radius: 14px !important;
  font-family: var(--font-body);
  font-weight: 700;
  font-size: 1rem;
}

/* ---- Responsive ---- */
@media(max-width:1100px) {
  .product-grid { grid-template-columns: repeat(3, 1fr); }
}
@media(max-width:800px) {
  .product-grid { grid-template-columns: repeat(2, 1fr); }
  .hero-title { font-size: 4rem; }
  .cat-list { grid-template-columns: 1fr; }
}
@media(max-width:500px) {
  .product-grid { grid-template-columns: 1fr 1fr; }
  .hero-title { font-size: 2.8rem; }
  .product-image { height: 140px; }
  .product-name { font-size: 1.1rem; }
  #cartBtn { width: 56px; height: 56px; font-size: 1.5rem; bottom: 16px; right: 16px; }
}
"""

# ============================================================
# TEMPLATE 3: Bistro Modern (resto-bistro)
# ============================================================
BISTRO_CSS = """
/* === BISTRO MODERN — Full Override === */
:root {
  --primary: #1565C0;
  --primary-dark: #0D47A1;
  --secondary: #E65100;
  --accent: #E65100;
  --surface: #FFFFFF;
  --surface-variant: #F5F7FA;
  --background: #F0F2F5;
  --text-strong: #263238;
  --text-soft: #607D8B;
  --text-disabled: #B0BEC5;
  --outline-variant: #E0E4E8;
  --font: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
  --fs-display: 2.5rem;
  --fs-headline: 1.75rem;
  --fs-title: 1.2rem;
  --fs-body: 0.95rem;
}

/* ---- Body ---- */
body { background: var(--background); font-family: var(--font); color: var(--text-strong); }

/* ---- Navigation: Clean White ---- */
.nav {
  background: #FFFFFF;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border-bottom: none;
}
.nav-inner { max-width: 1200px; }
.nav-brand {
  font-weight: 700;
  font-size: 1.2rem;
  color: var(--primary);
  letter-spacing: -0.5px;
}
.nav-link {
  font-weight: 600;
  font-size: 0.82rem;
  border-radius: 8px;
  color: var(--text-soft);
}
.nav-link:hover { background: #E3F2FD; color: var(--primary); }
.nav-link.active { background: var(--primary); color: #FFF !important; }

/* ---- Hero: Blue Gradient, Left-Aligned ---- */
.hero {
  background: linear-gradient(135deg, var(--primary) 0%, #1E88E5 100%);
  color: #FFFFFF;
  padding: 4.5rem 1.5rem;
  text-align: left;
}
.hero .container { max-width: 1200px; }
.hero-title {
  font-size: 3.2rem;
  font-weight: 800;
  letter-spacing: -1px;
  line-height: 1.1;
  margin-bottom: 0.75rem;
}
.hero-subtitle {
  font-size: 1.1rem;
  font-weight: 400;
  opacity: 0.9;
  margin-left: 0;
  max-width: 500px;
  margin-right: 0;
}
.hero .btn {
  background: var(--secondary);
  color: #FFF;
  border-radius: 8px;
  font-weight: 700;
  padding: 14px 32px;
  font-size: 0.9rem;
  transition: all 0.2s;
}
.hero .btn:hover { background: #BF360C; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(230,81,0,0.3); }

/* ---- Container ---- */
.container { max-width: 1200px; }

/* ---- Section Titles ---- */
.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-strong);
  margin-bottom: 1.5rem;
}

/* ---- Bistro Split Layout ---- */
.bistro-layout {
  display: flex;
  gap: 2rem;
  align-items: flex-start;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-md);
}
.bistro-sidebar {
  width: 260px;
  flex-shrink: 0;
  position: sticky;
  top: 80px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}
.bistro-sidebar-header {
  font-weight: 700;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--text-soft);
  padding: 0 1rem 0.75rem;
  margin-top: 2rem;
}
.bistro-sidebar .cat-list {
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.bistro-sidebar .cat-item {
  border-bottom: 1px solid #F0F2F5;
  padding: 0.9rem 1.25rem;
  transition: all 0.2s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  border-radius: 0;
  border-left: 3px solid transparent;
  background: #FFFFFF;
  margin: 0;
}
.bistro-sidebar .cat-item:last-child { border-bottom: none; }
.bistro-sidebar .cat-item:hover {
  background: #F5F8FC;
  border-left-color: var(--primary);
}
.bistro-sidebar .cat-item-active {
  background: #E3F2FD;
  border-left-color: var(--primary);
  font-weight: 700;
}
.bistro-sidebar .cat-item-name {
  font-size: 0.9rem;
  font-weight: 600;
  font-family: var(--font);
}
.bistro-sidebar .cat-item-count {
  background: #F0F2F5;
  color: var(--text-soft);
  font-weight: 600;
  font-size: 0.7rem;
  min-width: 28px;
  height: 22px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
}

.bistro-main { flex: 1; min-width: 0; }

/* ---- Product List View (Bistro) ---- */
.bistro-main .product-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.bistro-main .product-card {
  display: flex;
  padding: 1rem 1.25rem;
  gap: 1rem;
  background: #FFFFFF;
  border-radius: 0;
  border: none;
  border-bottom: 1px solid #EEF0F4;
  transition: all 0.2s ease;
  align-items: center;
  cursor: pointer;
}
.bistro-main .product-card:first-child {
  border-radius: 12px 12px 0 0;
}
.bistro-main .product-card:last-child {
  border-radius: 0 0 12px 12px;
  border-bottom: none;
}
.bistro-main .product-card:hover {
  background: #FAFBFC;
  padding-left: 1.75rem;
  border-left: 3px solid var(--primary);
}
.bistro-main .product-card.in-cart {
  background: #E3F2FD;
  border-left: 3px solid var(--primary);
}
.bistro-main .product-image {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
}
.bistro-main .product-info { flex: 1; padding: 0; }
.bistro-main .product-name {
  font-weight: 700;
  font-size: 0.95rem;
  margin-bottom: 2px;
  color: var(--text-strong);
}
.bistro-main .product-desc {
  font-size: 0.8rem;
  color: var(--text-soft);
  line-height: 1.4;
}
.bistro-main .product-price {
  font-size: 1rem;
  font-weight: 700;
  color: var(--secondary);
}
.bistro-main .product-actions {
  flex-shrink: 0;
  gap: 0.5rem;
  padding: 0;
  background: transparent;
}
.bistro-main .qty-btn {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  border: 1px solid #D0D5DD;
  color: #666;
  font-size: 0.9rem;
  background: #FFF;
  transition: all 0.2s;
}
.bistro-main .qty-btn:hover {
  background: var(--primary);
  color: #FFF;
  border-color: var(--primary);
}
.bistro-main .qty-value {
  font-weight: 700;
  font-size: 0.9rem;
  color: var(--text-strong);
}

/* ---- Cart Drawer ---- */
.drawer { background: #FFF; box-shadow: -4px 0 24px rgba(0,0,0,0.1); }
.drawer-header { border-bottom: 1px solid #EEE; }
.drawer-footer { border-top: 1px solid #EEE; }

/* ---- Footer ---- */
.footer {
  background: #FFFFFF;
  border-top: 1px solid var(--outline-variant);
  color: var(--text-soft);
  padding: 2.5rem var(--space-md);
}

/* ---- FAQ ---- */
.faq-item {
  background: #FFF;
  border-left: 3px solid var(--primary);
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.faq-question { font-weight: 700; }

/* ---- Contact ---- */
.contact-card {
  background: #FFF;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  border: 1px solid var(--outline-variant);
}

/* ---- Buttons (Global) ---- */
.btn-primary {
  background: var(--primary);
  color: #FFF;
  border-radius: 8px;
  font-weight: 700;
  transition: all 0.2s;
}
.btn-primary:hover { background: var(--primary-dark); }
.btn-outline {
  border: 1.5px solid var(--outline-variant);
  border-radius: 8px;
  font-weight: 600;
  color: var(--text-soft);
}
.btn-outline:hover { background: #F5F7FA; border-color: var(--primary); color: var(--primary); }

/* ---- Page Tabs ---- */
.page-tab { font-weight: 600; color: var(--text-soft); }
.page-tab.active { color: var(--primary); border-bottom-color: var(--primary); }
.page-subnav { border-bottom-color: var(--outline-variant); }

/* ---- Hours Table ---- */
.hours-table td { border-bottom-color: var(--outline-variant); }
.hours-table td:last-child { color: var(--text-strong); font-weight: 600; }

/* ---- Search Input (Non-bistro pages) ---- */
input[type="text"] {
  border-radius: 8px !important;
  border: 1.5px solid var(--outline-variant) !important;
  font-family: var(--font);
  font-size: 0.9rem;
  padding: 10px 14px;
  transition: border-color 0.2s;
}
input[type="text"]:focus { border-color: var(--primary) !important; outline: none; }

/* ---- Empty State ---- */
.empty-state { color: var(--text-disabled); }
.loading { color: var(--text-soft); }

/* ---- Responsive ---- */
@media(max-width:900px) {
  .bistro-layout { flex-direction: column; }
  .bistro-sidebar {
    width: 100%;
    position: static;
    max-height: none;
    overflow-y: visible;
  }
  .bistro-sidebar .cat-list { max-height: 300px; overflow-y: auto; }
  .bistro-main .product-card { padding: 0.85rem 1rem; }
  .hero { padding: 3rem 1rem; }
  .hero-title { font-size: 2.2rem; }
}
@media(max-width:500px) {
  .bistro-main .product-image { width: 48px; height: 48px; }
  .bistro-main .product-name { font-size: 0.85rem; }
  .bistro-main .product-desc { font-size: 0.75rem; }
  .bistro-main .product-price { font-size: 0.9rem; }
  .bistro-main .qty-btn { width: 26px; height: 26px; }
}
"""

PRESETS = [
    {
        "theme_id": "resto-luxe",
        "theme_name": "Fine Dining — Gastronomique",
        "type": "restaurant",
        "primary_color": "#C9A96E",
        "secondary_color": "#1C110A",
        "accent_color": "#C9A96E",
        "surface_color": "#FDF8F0",
        "background_color": "#FFFDF9",
        "font_heading": "Cormorant Garamond",
        "font_body": "Cormorant Garamond",
        "hero_title": "L'Écrin",
        "hero_subtitle": "Gastronomie étoilée au cœur de la ville",
        "hero_button_text": "Découvrir la carte",
        "custom_css": FINE_DINING_CSS,
    },
    {
        "theme_id": "resto-street",
        "theme_name": "Street Food — Urbain",
        "type": "restaurant",
        "primary_color": "#E63946",
        "secondary_color": "#FFD700",
        "accent_color": "#FFD700",
        "surface_color": "#FFFFFF",
        "background_color": "#F9F9F9",
        "font_heading": "Bebas Neue",
        "font_body": "Nunito",
        "hero_title": "STREET EATS",
        "hero_subtitle": "Saveurs du monde dans votre assiette",
        "hero_button_text": "Voir le menu",
        "custom_css": STREET_FOOD_CSS,
    },
    {
        "theme_id": "resto-bistro",
        "theme_name": "Bistro Modern — Contemporain",
        "type": "restaurant",
        "primary_color": "#1565C0",
        "secondary_color": "#E65100",
        "accent_color": "#E65100",
        "surface_color": "#FFFFFF",
        "background_color": "#F0F2F5",
        "font_heading": "Inter",
        "font_body": "Inter",
        "hero_title": "Le Bistro",
        "hero_subtitle": "Fast. Frais. Gourmand.",
        "hero_button_text": "Commander maintenant",
        "custom_css": BISTRO_CSS,
    },
]

# Insérer les presets (seul le premier est actif par défaut)
for i, p in enumerate(PRESETS):
    est_actif = (i == 0)  # Fine Dining actif par défaut
    cur.execute("""
        INSERT INTO theme_config (id, etablissement_id, theme_id, theme_name,
            primary_color, secondary_color, accent_color, surface_color, background_color,
            font_heading, font_body, hero_title, hero_subtitle, hero_button_text,
            custom_css, est_actif)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        str(uuid.uuid4()), eid, p["theme_id"], p["theme_name"],
        p["primary_color"], p["secondary_color"], p["accent_color"],
        p["surface_color"], p["background_color"],
        p["font_heading"], p["font_body"],
        p["hero_title"], p["hero_subtitle"], p["hero_button_text"],
        p["custom_css"], est_actif
    ))

conn.commit()

# Vérifier
cur.execute("""
    SELECT theme_id, theme_name,
           length(custom_css) as css_len, est_actif
    FROM theme_config WHERE deleted_at IS NULL ORDER BY theme_id
""")
rows = cur.fetchall()
print(f"{len(rows)} presets dans theme_config:")
for r in rows:
    css_kb = r[2] / 1000
    actif = "ACTIF" if r[3] else "inactif"
    print(f"  {r[0]:20s} {r[1]:35s} {css_kb:.1f}KB CSS  [{actif}]")

cur.close()
conn.close()
print("\nDone. Lance python sync_service.py pour synchroniser vers Supabase.")
